import warnings

# Filter specific Boto3/Python 3.9 deprecation warnings
warnings.filterwarnings("ignore", message=".*Boto3 will no longer support Python 3.9.*")
warnings.filterwarnings("ignore", category=DeprecationWarning)

import logging
import sys
import argparse
import boto3
from concurrent.futures import ThreadPoolExecutor, as_completed
from utils.regions import list_regions
from output.writer import write_output

# Import collectors
from collectors.ec2 import collect_ec2_instances
from collectors.ebs import collect_ebs_volumes
from collectors.s3 import collect_s3_buckets
from collectors.lambda_functions import collect_lambda_functions
from collectors.asgConverter import collect_asg_as_ec2_equivalent

# Organized Logging Configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [%(account_id)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("CloudScanner")


def log_info(msg, account_id="SYSTEM"):
    logger.info(msg, extra={'account_id': account_id})


def log_warn(msg, account_id="SYSTEM"):
    logger.warning(msg, extra={'account_id': account_id})


def is_management_account():
    """Detects if running from the organization management account."""
    try:
        org = boto3.client('organizations')
        org_info = org.describe_organization()['Organization']
        sts = boto3.client('sts')
        current_id = sts.get_caller_identity()['Account']
        return current_id == org_info.get('MasterAccountId') or current_id == org_info.get('ManagementAccountId')
    except Exception:
        return False


def get_accounts():
    """Fetches active member accounts from the organization."""
    try:
        org = boto3.client("organizations")
        accounts = []
        paginator = org.get_paginator("list_accounts")
        for page in paginator.paginate():
            for acc in page.get("Accounts", []):
                state = acc.get("State") or acc.get("Status")
                if state == "ACTIVE":
                    accounts.append({"id": acc["Id"], "name": acc["Name"]})
        return accounts
    except Exception:
        log_info("Running from member account or missing organizations:ListAccounts permission", "SYSTEM")
        return None


def get_assumed_session(account_id, role_name):
    """Assumes role in member account."""
    sts = boto3.client("sts")
    role_arn = f"arn:aws:iam::{account_id}:role/{role_name}"
    try:
        response = sts.assume_role(RoleArn=role_arn, RoleSessionName="Scanner")
        creds = response["Credentials"]
        return boto3.Session(
            aws_access_key_id=creds["AccessKeyId"],
            aws_secret_access_key=creds["SecretAccessKey"],
            aws_session_token=creds["SessionToken"]
        )
    except Exception:
        return None


def scan_region_logic(session, region, account_id):
    """
    Aggregates all regional findings into a single flat list.
    Returns: (list_of_resources, list_of_permission_errors)
    """
    region_results = []
    region_errors = set()

    collectors = [
        collect_ec2_instances,
        collect_ebs_volumes,
        collect_lambda_functions,
        collect_asg_as_ec2_equivalent
    ]

    for collector in collectors:
        data, error = collector(session, region, account_id)
        if data:
            region_results.extend(data)
        if error:
            region_errors.add(error)

    return region_results, list(region_errors)


def scan_account(account_info, role_name, is_mgmt_node=False):
    account_id = account_info["id"]
    name = account_info["name"]
    suffix = " [Management Account]" if is_mgmt_node else ""

    log_info(f"Starting scan for account: {name} ({account_id}){suffix}", account_id)

    # Session Setup
    sts = boto3.client("sts")
    curr_id = sts.get_caller_identity()["Account"]
    if account_id == curr_id:
        session = boto3.Session()
    else:
        # Pass the custom role name here
        session = get_assumed_session(account_id, role_name)
        if not session:
            log_warn(f"Skipping {name}: {role_name} missing or untrusted.", account_id)
            return []

    account_results = []
    account_errors = set()

    # S3 Scan (Global)
    try:
        s3_data, s3_err = collect_s3_buckets(session, account_id)
        if s3_data: account_results.extend(s3_data)
        if s3_err: account_errors.add(s3_err)
    except Exception:
        pass

    # Regional Scans
    account_regions = list_regions(session)
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(scan_region_logic, session, r, account_id) for r in account_regions]
        for f in as_completed(futures):
            r_data, r_errors = f.result()
            if r_data:
                account_results.extend(r_data)
            if r_errors:
                account_errors.update(r_errors)

    # Summary Logging for Permissions
    if account_errors:
        formatted_errors = ", ".join(sorted(account_errors))
        log_warn(f"Partial scan. Missing permissions: {formatted_errors}", account_id)

    log_info(f"Scan complete. Found {len(account_results)} resources.", account_id)
    return account_results


def main():
    # Argument Parsing
    parser = argparse.ArgumentParser(description="Cloud Scanner & Cost Estimator")
    parser.add_argument("--role", type=str, default="OrganizationAccountAccessRole",
                        help="The IAM Role name to assume in member accounts (default: OrganizationAccountAccessRole)")
    args = parser.parse_args()

    is_mgmt = is_management_account()
    if not is_mgmt:
        log_info("Running from a Member Account. Multi-account discovery is disabled.", "SYSTEM")

    all_results = []
    accounts = get_accounts() if is_mgmt else None

    # Determine list of accounts to scan
    scan_list = []
    if accounts:
        scan_list = accounts
    else:
        # Local fallback
        sts = boto3.client("sts")
        curr_id = sts.get_caller_identity()["Account"]
        scan_list = [{"id": curr_id, "name": "Local-Account"}]

    # Tracking metrics
    total_accounts = len(scan_list)
    full_success_count = 0
    partial_count = 0

    # Execution Loop
    for acc in scan_list:
        print("")  # Line break between accounts for visibility

        try:
            sts = boto3.client("sts")
            curr_id = sts.get_caller_identity()["Account"]
            is_node = (acc["id"] == curr_id)

            # Execute Scan with the role argument
            results = scan_account(acc, args.role, is_node)
            all_results.extend(results)

            if len(results) == 0:
                partial_count += 1
            else:
                full_success_count += 1

        except Exception as e:
            log_warn(f"Failed to scan {acc['name']}: {str(e)}", acc['id'])

    # Final Summary
    print("")  # Final line break
    log_info(
        f"Summary: {full_success_count} full scans, {partial_count} partial/empty scans out of {total_accounts} total.",
        "SYSTEM")

    # WRITE OUTPUT
    write_output(all_results)


if __name__ == "__main__":
    main()
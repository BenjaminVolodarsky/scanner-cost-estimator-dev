import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning, module="boto3")
import logging
import sys
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

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [%(account_id)s] %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("CloudScanner")


def log_info(msg, account_id="SYSTEM"):
    logger.info(msg, extra={'account_id': account_id})


def log_warn(msg, account_id="SYSTEM"):
    logger.warning(msg, extra={'account_id': account_id})


def is_management_account():
    try:
        org = boto3.client('organizations')
        org_info = org.describe_organization()['Organization']
        sts = boto3.client('sts')
        current_id = sts.get_caller_identity()['Account']
        return current_id == org_info.get('MasterAccountId') or current_id == org_info.get('ManagementAccountId')
    except Exception:
        return False


def get_accounts():
    try:
        org = boto3.client("organizations")
        accounts = []
        paginator = org.get_paginator("list_accounts")
        for page in paginator.paginate():
            for acc in page.get("Accounts", []):
                if acc.get("Status") == "ACTIVE":
                    accounts.append({"id": acc["Id"], "name": acc["Name"]})
        return accounts
    except Exception:
        log_info("Running from member account or missing organizations:ListAccounts permission", "SYSTEM")
        return None


def get_assumed_session(account_id):
    sts = boto3.client("sts")
    role_arn = f"arn:aws:iam::{account_id}:role/OrganizationAccountAccessRole"
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
    Returns a tuple: (list_of_resources, list_of_permission_errors)
    """
    region_results = []
    region_errors = set()

    # Call collectors. Each MUST return (data_list, error_str_or_None)
    for collector in [collect_ec2_instances, collect_ebs_volumes, collect_lambda_functions,
                      collect_asg_as_ec2_equivalent]:
        data, error = collector(session, region, account_id)
        if data:
            region_results.extend(data)
        if error:
            region_errors.add(error)

    return region_results, list(region_errors)


def scan_account(account_info, is_mgmt_node=False):
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
        session = get_assumed_session(account_id)
        if not session:
            log_warn(f"Skipping {name}: OrganizationAccountAccessRole missing or untrusted.", account_id)
            return []

    account_results = []
    account_errors = set()

    # S3 Scan (Global)
    s3_data, s3_err = collect_s3_buckets(session, account_id)
    if s3_data: account_results.extend(s3_data)
    if s3_err: account_errors.add(s3_err)

    # Regional Scans
    account_regions = list_regions(session)
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(scan_region_logic, session, r, account_id) for r in account_regions]
        for f in as_completed(futures):
            r_data, r_errors = f.result()
            # 1. Flatten Data: extend() prevents nested lists (Fixes CSV error)
            if r_data:
                account_results.extend(r_data)
            # 2. Collect Errors: Add to set for deduplication (Fixes Log Spam)
            if r_errors:
                account_errors.update(r_errors)

    # Summary Logging
    if account_errors:
        # Sort errors for clean reading
        formatted_errors = ", ".join(sorted(account_errors))
        log_warn(f"Partial scan. Missing permissions: {formatted_errors}", account_id)

    log_info(f"Scan complete. Found {len(account_results)} resources.", account_id)
    return account_results


def main():
    is_mgmt = is_management_account()
    if not is_mgmt:
        log_info("Running from a Member Account. Multi-account discovery is disabled.", "SYSTEM")

    all_results = []
    accounts = get_accounts() if is_mgmt else None

    if accounts:
        for acc in accounts:
            sts = boto3.client("sts")
            is_node = (acc["id"] == sts.get_caller_identity()["Account"])
            all_results.extend(scan_account(acc, is_node))
    else:
        sts = boto3.client("sts")
        curr_id = sts.get_caller_identity()["Account"]
        all_results.extend(scan_account({"id": curr_id, "name": "Local-Account"}, is_mgmt))

    write_output(all_results)


if __name__ == "__main__":
    main()
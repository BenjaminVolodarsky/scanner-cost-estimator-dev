import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning, module="boto3")
import logging
import sys
import boto3
from concurrent.futures import ThreadPoolExecutor, as_completed
from utils.regions import list_regions
from utils.spinner import start_spinner, stop_spinner
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
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("CloudScanner")


def log_info(msg, account_id="SYSTEM"):
    logger.info(msg, extra={'account_id': account_id})


def is_management_account():
    """Detects if running from the organization management account."""
    try:
        org = boto3.client('organizations')
        org_info = org.describe_organization()['Organization']
        sts = boto3.client('sts')
        current_id = sts.get_caller_identity()['Account']
        # Return True if current ID matches the Management (Master) ID
        return current_id == org_info['MasterAccountId']
    except Exception:
        # Fails if not in an Org or missing permissions
        return False


def get_accounts():
    """Fetches active member accounts from the organization."""
    org = boto3.client("organizations")
    accounts = []
    try:
        paginator = org.get_paginator("list_accounts")
        for page in paginator.paginate():
            for acc in page.get("Accounts", []):
                # Using 2026-ready state check
                state = acc.get("State") or acc.get("Status")
                if state == "ACTIVE":
                    accounts.append({"id": acc["Id"], "name": acc["Name"]})
        return accounts
    except Exception as e:
        log_info(f"failed Starting scan for member accounts - sts:assumeRole on the management account is not enabled",
                 "SYSTEM")
        return None


def get_assumed_session(account_id, role_name="OrganizationAccountAccessRole"):
    """Assumes a role in a member account and returns a new session."""
    sts = boto3.client("sts")
    role_arn = f"arn:aws:iam::{account_id}:role/{role_name}"
    try:
        response = sts.assume_role(RoleArn=role_arn, RoleSessionName="CloudScannerEstimator")
        creds = response["Credentials"]
        return boto3.Session(
            aws_access_key_id=creds["AccessKeyId"],
            aws_secret_access_key=creds["SecretAccessKey"],
            aws_session_token=creds["SessionToken"]
        )
    except Exception:
        return None


def scan_account(account_info, is_mgmt_node=False):
    account_id = account_info["id"]
    name = account_info["name"]
    suffix = " [Management Account]" if is_mgmt_node else ""

    log_info(f"Starting scan for account: {name} ({account_id}){suffix}", account_id)

    try:
        sts = boto3.client("sts")
        curr_id = sts.get_caller_identity()["Account"]

        # Use local session if it is the current account
        if account_id == curr_id:
            session = boto3.Session()
        else:
            session = get_assumed_session(account_id)
            if not session:
                log_info(
                    f"failed Starting scan for account: {name} ({account_id}) - OrganizationAccountAccessRole missing",
                    account_id)
                return []

        account_regions = list_regions(session)
        account_results = []

        # S3 is a global service; scan once per account
        account_results.extend(collect_s3_buckets(session, account_id))

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(scan_region_logic, session, r, account_id) for r in account_regions]
            for f in as_completed(futures):
                region_data = f.result()
                # Fixed aggregation: merge lists rather than nesting
                if isinstance(region_data, list):
                    account_results.extend(region_data)

        log_info(f"Scan complete. Found {len(account_results)} resources.", account_id)
        return account_results
    except Exception:
        return []


def scan_region_logic(session, region, account_id):
    """Aggregates all regional findings into a single flat list."""
    region_results = []
    # Collectors return flat lists; use extend to keep them merged
    region_results.extend(collect_ec2_instances(session, region, account_id))
    region_results.extend(collect_ebs_volumes(session, region, account_id))
    region_results.extend(collect_lambda_functions(session, region, account_id))
    region_results.extend(collect_asg_as_ec2_equivalent(session, region, account_id))
    return region_results


def main():
    is_mgmt = is_management_account()
    if not is_mgmt:
        log_info("Running from a Member Account. Multi-account discovery is disabled.", "SYSTEM")

    all_results = []
    accounts = get_accounts() if is_mgmt else None

    if accounts:
        for acc in accounts:
            sts = boto3.client("sts")
            is_mgmt_node = (acc["id"] == sts.get_caller_identity()["Account"])
            all_results.extend(scan_account(acc, is_mgmt_node))
    else:
        # Fallback to local scan if not in a Management account
        sts = boto3.client("sts")
        curr_id = sts.get_caller_identity()["Account"]
        all_results.extend(scan_account({"id": curr_id, "name": "Local-Account"}, is_mgmt))

    write_output(all_results)


if __name__ == "__main__":
    main()
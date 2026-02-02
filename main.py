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

def get_accounts():
    """Always fetches all active accounts using 2026-ready state checks."""
    org = boto3.client("organizations")
    accounts = []
    try:
        paginator = org.get_paginator("list_accounts")
        for page in paginator.paginate():
            for acc in page.get("Accounts", []):
                state = acc.get("State") or acc.get("Status")
                if state == "ACTIVE":
                    accounts.append({"id": acc["Id"], "name": acc["Name"]})
    except Exception as e:
        # If listing fails, we fall back to just the local account
        return None
    return accounts

def get_assumed_session(account_id, role_name="OrganizationAccountAccessRole"):
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


def scan_account(account_info):
    account_id = account_info["id"]
    account_name = account_info.get("name", "Unknown")

    log_info(f"Starting scan for account: {account_name} ({account_id})", account_id)

    try:
        sts_client = boto3.client("sts")
        current_account_id = sts_client.get_caller_identity()["Account"]

        if account_id == current_account_id:
            session = boto3.Session()
        else:
            session = get_assumed_session(account_id)

        if not session:
            log_warn("Access denied: Could not assume role. Verify trust relationship.", account_id)
            return []

        # Get enabled regions for this account
        account_regions = list_regions(session)
        account_results = []

        # Track permission issues silently
        permission_gaps = set()

        # Global S3 Scan
        account_results += collect_s3_buckets(session, account_id)

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(scan_region_logic, session, r, account_id) for r in account_regions]
            for f in as_completed(futures):
                res, gaps = f.result()  # Collectors now return (data, gaps)
                account_results += res
                permission_gaps.update(gaps)

        if permission_gaps:
            log_warn(f"Limited visibility. Missing policies: {', '.join(sorted(permission_gaps))}", account_id)

        log_info(f"Scan complete. Found {len(account_results)} resources.", account_id)
        return account_results

    except Exception as e:
        return []


def scan_region_logic(session, region, account_id):
    region_results = []
    gaps = []

    # Each collector now handles AccessDenied gracefully and reports it back
    res_ec2, gap_ec2 = collect_ec2_instances(session, region, account_id)
    region_results += res_ec2
    if gap_ec2: gaps.append(gap_ec2)

    res_ebs, gap_ebs = collect_ebs_volumes(session, region, account_id)
    region_results += res_ebs
    if gap_ebs: gaps.append(gap_ebs)

    res_lam, gap_lam = collect_lambda_functions(session, region, account_id)
    region_results += res_lam
    if gap_lam: gaps.append(gap_lam)

    return region_results, gaps


def main():
    all_results = []
    start_spinner()

    accounts = get_accounts()
    if accounts:
        for acc in accounts:
            # regions is no longer passed as an argument
            all_results += scan_account(acc)
    else:
        curr_id = boto3.client("sts").get_caller_identity()["Account"]
        all_results += scan_account({"id": curr_id, "name": "Local-Account"})

    stop_spinner()
    write_output(all_results)

if __name__ == "__main__":
    main()
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
    handlers=[
        logging.FileHandler("scanner_debug.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("CloudScanner")

# Helper to log with account context
def log_info(msg, account_id="N/A"):
    logger.info(msg, extra={'account_id': account_id})

def log_error(msg, account_id="N/A"):
    logger.error(msg, extra={'account_id': account_id})

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


def scan_account(account_info, regions):
    account_id = account_info["id"]
    account_name = account_info.get("name", "Unknown")

    log_info(f"🚀 Starting scan for {account_name}", account_id)

    try:
        # Identify current caller to decide if we need to AssumeRole
        sts_client = boto3.client("sts")
        current_identity = sts_client.get_caller_identity()
        current_account_id = current_identity["Account"]

        if account_id == current_account_id:
            log_info("🏠 Using local session (no AssumeRole needed)", account_id)
            session = boto3.Session()
        else:
            log_info(f"🔑 Attempting AssumeRole into {account_id}", account_id)
            session = get_assumed_session(account_id)

        if not session:
            log_error("❌ Failed to create session. Skipping account.", account_id)
            return []

        # Double-check identity within the new session
        verified_id = session.client("sts").get_caller_identity()["Account"]
        log_info(f"✅ Session verified for account: {verified_id}", verified_id)

        # MOVED INSIDE TRY: Start collecting data
        account_results = []
        account_results += collect_s3_buckets(session, account_id)

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(scan_region_logic, session, r, account_id) for r in regions]
            for f in as_completed(futures):
                account_results += f.result()

        return account_results  # Success return

    except Exception as e:
        log_error(f"💥 Unexpected error in scan_account: {str(e)}", account_id)
        return []


def scan_region_logic(session, region, account_id):
    region_results = []
    region_results += collect_ec2_instances(session, region, account_id)
    region_results += collect_asg_as_ec2_equivalent(session, region, account_id)
    region_results += collect_ebs_volumes(session, region, account_id)
    region_results += collect_lambda_functions(session, region, account_id)
    return region_results

def main():
    regions = list_regions()
    all_results = []

    start_spinner()

    accounts = get_accounts()
    if accounts:
        # If we can see the Org, scan everything
        for acc in accounts:
            all_results += scan_account(acc, regions)
    else:
        # Fallback to local account if not in a Management account
        curr_id = boto3.client("sts").get_caller_identity()["Account"]
        all_results += scan_account({"id": curr_id, "name": "Local-Account"}, regions)

    stop_spinner()
    write_output(all_results)

if __name__ == "__main__":
    main()
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

# Clean, organized logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [%(account_id)s] %(message)s',
    handlers=[
        logging.FileHandler("scanner_debug.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("CloudScanner")


def log_info(msg, account_id="SYSTEM"):
    logger.info(msg, extra={'account_id': account_id})


def log_error(msg, account_id="SYSTEM"):
    logger.error(msg, extra={'account_id': account_id})


def get_accounts():
    """Fetches all active accounts from AWS Organizations."""
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
        return None


def get_assumed_session(account_id, role_name="OrganizationAccountAccessRole"):
    """Assumes the administrative role in a member account."""
    sts = boto3.client("sts")
    role_arn = f"arn:aws:iam::{account_id}:role/{role_name}"
    try:
        response = sts.assume_role(
            RoleArn=role_arn,
            RoleSessionName="CloudScannerEstimator"
        )
        creds = response["Credentials"]
        return boto3.Session(
            aws_access_key_id=creds["AccessKeyId"],
            aws_secret_access_key=creds["SecretAccessKey"],
            aws_session_token=creds["SessionToken"]
        )
    except Exception:
        return None


def scan_region_logic(session, region, account_id):
    """Executes all regional collectors and returns a single combined list."""
    region_results = []

    # Each collector is called with the current session and account ID
    region_results.extend(collect_ec2_instances(session, region, account_id))
    region_results.extend(collect_asg_as_ec2_equivalent(session, region, account_id))
    region_results.extend(collect_ebs_volumes(session, region, account_id))
    region_results.extend(collect_lambda_functions(session, region, account_id))

    return region_results


def scan_account(account_info):
    """Handles session establishment and data aggregation for a single account."""
    account_id = account_info["id"]
    account_name = account_info.get("name", "Unknown")

    log_info(f"Starting scan for account: {account_name} ({account_id})", account_id)

    try:
        sts_client = boto3.client("sts")
        current_account_id = sts_client.get_caller_identity()["Account"]

        # 1. Establish Session
        if account_id == current_account_id:
            session = boto3.Session()
        else:
            session = get_assumed_session(account_id)

        if not session:
            log_error("Failed to establish session. Check IAM trust policy.", account_id)
            return []

        # 2. Identify Enabled Regions
        account_regions = list_regions(session)
        account_results = []

        # 3. Global Scans (S3)
        account_results.extend(collect_s3_buckets(session, account_id))

        # 4. Regional Scans via Thread Pool
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [
                executor.submit(scan_region_logic, session, r, account_id)
                for r in account_regions
            ]
            for f in as_completed(futures):
                # Retrieve and aggregate the data from each thread
                result_data = f.result()
                if result_data:
                    account_results.extend(result_data)

        log_info(f"Scan complete. Found {len(account_results)} resources.", account_id)
        return account_results

    except Exception as e:
        log_error(f"Unexpected account error: {str(e)}", account_id)
        return []


def main():
    """Main entry point for the cross-account scanner."""
    all_results = []

    # 1. Discovery
    accounts = get_accounts()

    # 2. Execution
    if accounts:
        for acc in accounts:
            all_results.extend(scan_account(acc))
    else:
        # Fallback if Organizations access is restricted
        sts = boto3.client("sts")
        curr_id = sts.get_caller_identity()["Account"]
        all_results.extend(scan_account({"id": curr_id, "name": "Local-Account"}))

    # 3. Output Generation
    write_output(all_results)


if __name__ == "__main__":
    main()
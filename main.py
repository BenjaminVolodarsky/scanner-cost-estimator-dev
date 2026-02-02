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


def is_management_account():
    org = boto3.client('organizations')
    try:
        org_info = org.describe_organization()['Organization']
        sts = boto3.client('sts')
        current_id = sts.get_caller_identity()['Account']
        return current_id == org_info['ManagementAccountId']
    except Exception:
        return False


def get_assumed_session(account_id):
    sts = boto3.client("sts")
    role_arn = f"arn:aws:iam::{account_id}:role/OrganizationAccountAccessRole"
    try:
        response = sts.assume_role(RoleArn=role_arn, RoleSessionName="Scanner")
        return boto3.Session(
            aws_access_key_id=response["Credentials"]["AccessKeyId"],
            aws_secret_access_key=response["Credentials"]["SecretAccessKey"],
            aws_session_token=response["Credentials"]["SessionToken"]
        )
    except Exception as e:
        if "AccessDenied" in str(e):
            # This handles your specific request for management-side STS failures
            log_info(
                f"failed Starting scan for member accounts - sts:assumeRole on the management account is not enabled",
                "SYSTEM")
        return None


def scan_account(account_info, is_mgmt_node):
    account_id = account_info["id"]
    name = account_info["name"]
    suffix = " [Management Account]" if is_mgmt_node else ""

    log_info(f"Starting scan for account: {name} ({account_id}){suffix}", account_id)

    # Establish session
    sts = boto3.client("sts")
    curr_id = sts.get_caller_identity()["Account"]

    if account_id == curr_id:
        session = boto3.Session()
    else:
        session = get_assumed_session(account_id)
        if not session:
            log_info(f"failed Starting scan for account: {name} ({account_id}) - OrganizationAccountAccessRole missing",
                     account_id)
            return []

    account_results = []
    # Use extend() to keep the list flat and avoid the 'keys' AttributeError
    account_results.extend(collect_s3_buckets(session, account_id))

    account_regions = list_regions(session)
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(scan_region_logic, session, r, account_id) for r in account_regions]
        for f in as_completed(futures):
            # Fixed aggregation to avoid nested lists
            account_results.extend(f.result())

    log_info(f"Scan complete. Found {len(account_results)} resources.", account_id)
    return account_results


def scan_region_logic(session, region, account_id):
    res = []
    # We call these and let them log their own specific permission gaps
    res.extend(collect_ec2_instances(session, region, account_id))
    res.extend(collect_asg_as_ec2_equivalent(session, region, account_id))
    res.extend(collect_ebs_volumes(session, region, account_id))
    res.extend(collect_lambda_functions(session, region, account_id))
    return res


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
        sts = boto3.client("sts")
        curr_id = sts.get_caller_identity()["Account"]
        all_results.extend(scan_account({"id": curr_id, "name": "Local-Account"}, False))

    write_output(all_results)


if __name__ == "__main__":
    main()
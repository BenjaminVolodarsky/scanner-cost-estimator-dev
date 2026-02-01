import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning, module="boto3")

import boto3
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from utils.regions import list_regions
from utils.spinner import start_spinner, stop_spinner
from output.writer import write_output

# Import your collectors
from collectors.ec2 import collect_ec2_instances
from collectors.ebs import collect_ebs_volumes
from collectors.s3 import collect_s3_buckets
from collectors.lambda_functions import collect_lambda_functions
from collectors.asgConverter import collect_asg_as_ec2_equivalent


def get_accounts():
    """Fetches all active AWS account IDs with full pagination and 2026 state checks."""
    org = boto3.client("organizations")
    accounts = []
    try:
        paginator = org.get_paginator("list_accounts")
        # Ensure we iterate through every single page
        for page in paginator.paginate():
            for acc in page.get("Accounts", []):
                # Check 'State' (recommended for 2026) or fallback to 'Status'
                state = acc.get("State") or acc.get("Status")
                if state == "ACTIVE":
                    print(f"✅ Found active account: {acc['Name']} ({acc['Id']})")
                    accounts.append({"id": acc["Id"], "name": acc["Name"]})

        if not accounts:
            print("⚠️ Organizations returned 0 active accounts. Check your management account permissions.")
    except Exception as e:
        print(f"❌ Error listing accounts: {e}")
        return None
    return accounts


def get_assumed_session(account_id, role_name="OrganizationAccountAccessRole"):
    """Creates a boto3 session by assuming a role in a target account."""
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
    except Exception as e:
        print(f"⚠️ Could not assume role in {account_id}: {e}")
        return None


def scan_account(account_info, regions, args):
    account_id = account_info["id"]
    current_account_id = boto3.client("sts").get_caller_identity()["Account"]

    # If scanning the same account we are logged into, use the current session directly
    if account_id == current_account_id:
        print(f"🏠 Scanning Local Account: {account_info['name']} ({account_id})...")
        session = boto3.Session()  # Use current environment credentials
    else:
        print(f"🔎 Scanning Remote Account: {account_info['name']} ({account_id})...")
        session = get_assumed_session(account_id)

    if not session:
        print(f"  ❌ Failed: Could not assume role in {account_id}")
        return []

    account_results = []
    # Collect S3 (Global) once per account
    s3_data = collect_s3_buckets(session, account_id)
    account_results += s3_data

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(scan_region_logic, session, r, args, account_id) for r in regions]
        for f in as_completed(futures):
            account_results += f.result()

    print(f"  ✅ Done: Found {len(account_results)} items in {account_id}")
    return account_results


def scan_region_logic(session, region, args, account_id):
    """Orchestrates all regional collection for a specific account."""
    region_results = []

    # 1. Collect EC2 Instances
    region_results += collect_ec2_instances(session, region, args, account_id)

    # 2. Collect ASGs (as single VM targets)
    region_results += collect_asg_as_ec2_equivalent(session, region, args, account_id)

    # 3. Collect EBS Volumes
    region_results += collect_ebs_volumes(session, region, args, account_id)

    # 4. Collect Lambda Functions
    region_results += collect_lambda_functions(session, region, args, account_id)

    return region_results


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--all-accounts", action="store_true", help="Scan entire AWS Organization")
    # Added missing flags for your collectors
    parser.add_argument("--include-stopped", action="store_true", help="Include stopped EC2 instances")
    parser.add_argument("--include-k8s-asg", action="store_true", help="Include Kubernetes-tagged ASGs")
    args = parser.parse_args()

    regions = list_regions()
    all_results = []

    start_spinner()

    if args.all_accounts:
        accounts = get_accounts()
        if accounts:
            for acc in accounts:
                all_results += scan_account(acc, regions, args)
    else:
        # IMPORTANT: If no flag is passed, scan the local account
        current_account_id = boto3.client("sts").get_caller_identity()["Account"]
        current_info = {"id": current_account_id, "name": "Local-Account"}
        all_results += scan_account(current_info, regions, args)

    stop_spinner()
    write_output(all_results)


if __name__ == "__main__":
    main()
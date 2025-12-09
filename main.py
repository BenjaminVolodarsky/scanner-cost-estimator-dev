#!/usr/bin/env python3

from utils.regions import list_regions
from utils.accounts import list_org_accounts, find_assumable_role
from collectors.ec2 import collect_ec2_instances
from collectors.ebs import collect_ebs_volumes
from collectors.s3 import collect_s3_buckets
from collectors.asg import collect_auto_scaling_groups
from output.writer import write_output

import boto3
from concurrent.futures import ThreadPoolExecutor, as_completed


def scan_account(account_id):
    """Assume available role automatically + scan all regions."""
    print(f"\n📂 Scanning Account: {account_id}")

    session = find_assumable_role(account_id)
    if not session:
        print(f"❌ No assumable role found → Skipping account {account_id}")
        return []

    results = []
    regions = list_regions()

    def scan_region(region):
        try:
            print(f"   🌍 {account_id} → {region}")

            sess = session.Session(
                region_name=region
            )

            return (
                collect_ec2_instances(sess, region) +
                collect_ebs_volumes(sess, region) +
                collect_s3_buckets(sess, region) +
                collect_auto_scaling_groups(sess, region)
            )
        except Exception as e:
            print(f"⚠️  {account_id}/{region} failed: {e}")
            return []

    with ThreadPoolExecutor(max_workers=10):  # parallel regions
        futures = {executor.submit(scan_region, r): r for r in regions}
        for future in as_completed(futures):
            results += future.result()

    return results



def main():
    print("\n🚀 Upwind CloudScanner Cost Estimator\n")
    sts = boto3.client("sts")
    identity = sts.get_caller_identity()
    print(f"🏢 Management Account: {identity['Account']}")

    print("\n🔍 Discovering accounts via AWS Organizations...\n")
    accounts = list_org_accounts()
    print(f"📁 Found {len(accounts)} accounts to scan")

    all_data = []

    with ThreadPoolExecutor(max_workers=4):  # parallel per account
        futures = {executor.submit(scan_account, acc["account_id"]): acc for acc in accounts}
        for future in as_completed(futures):
            all_data += future.result()

    print(f"\n✔ Scan complete. Total assets: {len(all_data)}")

    write_output(all_data, "upwind_org_report.json", "upwind_org_report.csv")

    print("\n📄 Saved results:")
    print("  🔸 upwind_org_report.json")
    print("  🔸 upwind_org_report.csv\n")


if __name__ == "__main__":
    main()

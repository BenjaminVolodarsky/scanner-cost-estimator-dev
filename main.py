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
    """Scan all regions for a member account."""
    print(f"\n📂 Scanning AWS Account {account_id}")

    session = find_assumable_role(account_id)
    if not session:
        print(f"❌ No assumable role exists in {account_id} — skipping")
        return []

    regions = list_regions()
    results = []

    def scan_region(region):
        try:
            sess = session.Session(region_name=region)
            print(f"   🌍 {account_id} → {region}")

            return (
                collect_ec2_instances(sess, region) +
                collect_ebs_volumes(sess, region) +
                collect_s3_buckets(sess, region) +
                collect_auto_scaling_groups(sess, region)
            )
        except:
            return []

    with ThreadPoolExecutor(max_workers=10):    # parallel per region
        futures = [executor.submit(scan_region, r) for r in regions]
        for f in as_completed(futures):
            results += f.result()

    return results


def main():
    print("\n🚀 Upwind CloudScanner Cost Estimator\n")
    sts = boto3.client("sts")
    identity = sts.get_caller_identity()
    print(f"🏢 Management Account: {identity['Account']}")

    accounts = list_org_accounts()
    print(f"📁 {len(accounts)} accounts discovered in org")

    all_data = []

    with ThreadPoolExecutor(max_workers=4):     # parallel per account
        futures = [executor.submit(scan_account, acc["account_id"]) for acc in accounts]
        for f in as_completed(futures):
            all_data += f.result()

    print(f"\n✔ Scan complete — total resources: {len(all_data)}")
    write_output(all_data, "upwind_org_report.json", "upwind_org_report.csv")
    print("\n📄 Reports saved → upwind_org_report.json / upwind_org_report.csv")


if __name__ == "__main__":
    main()

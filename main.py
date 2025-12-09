#!/usr/bin/env python3

import boto3
from utils.regions import list_regions
from collectors.ec2 import collect_ec2_instances
from collectors.ebs import collect_ebs_volumes
from collectors.s3 import collect_s3_buckets
from collectors.asg import collect_auto_scaling_groups
from output.writer import write_output

from concurrent.futures import ThreadPoolExecutor, as_completed


def scan_region(region):
    """Scan a single AWS region for resources"""
    print(f"🌍 Scanning region: {region}")
    session = boto3.Session(region_name=region)

    try:
        return (
            collect_ec2_instances(session, region) +
            collect_ebs_volumes(session, region) +
            collect_s3_buckets(session, region) +       # bucket metadata (not size)
            collect_auto_scaling_groups(session, region)
        )
    except Exception as e:
        print(f"⚠️  Failed scanning region {region} → {e}")
        return []


def main():
    print("\n🚀 Upwind CloudScanner Cost Estimator\n")

    sts = boto3.client("sts")
    identity = sts.get_caller_identity()
    print(f"🏢 Account: {identity['Account']}\n")

    regions = list_regions()
    results = []

    # Scan regions in parallel (fast)
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(scan_region, r) for r in regions]
        for f in as_completed(futures):
            results += f.result()

    print(f"\n✔ Scan complete — resources collected: {len(results)}")

    write_output(results,
        json_file="upwind_report.json",
        csv_file="upwind_report.csv"
    )

    print("\n📄 Output saved:")
    print("   📁 upwind_report.json")
    print("   📁 upwind_report.csv\n")


if __name__ == "__main__":
    main()

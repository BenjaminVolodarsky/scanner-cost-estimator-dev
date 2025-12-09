#!/usr/bin/env python3

from utils.regions import list_regions
from collectors.ec2 import collect_ec2_instances
from collectors.ebs import collect_ebs_volumes
from collectors.s3 import collect_s3_buckets
from collectors.asg import collect_auto_scaling_groups
from output.writer import write_output
import boto3

def main():
    print("\n🚀 Upwind CloudScanner Cost Estimator\n")
    sts = boto3.client("sts")
    identity = sts.get_caller_identity()
    print(f"🏢 Running in AWS Account: {identity['Account']}\n")

    all_data = []
    regions = list_regions()

    for region in regions:
        print(f"🌍 Scanning region: {region}")
        session = boto3.Session(region_name=region)

        all_data += collect_ec2_instances(session, region)
        all_data += collect_ebs_volumes(session, region)
        all_data += collect_auto_scaling_groups(session, region)

    # S3 is GLOBAL, do once — not per region
    print("\n📦 Collecting S3 Buckets globally...")
    session_global = boto3.Session(region_name="us-east-1")
    all_data += collect_s3_buckets(session_global)

    print(f"\n✔ Done. Total collected items: {len(all_data)}")
    write_output(all_data,
        json_name="upwind_report.json",
        csv_name="upwind_report.csv"
    )
    print("\n📄 Output saved → upwind_report.json / upwind_report.csv\n")

if __name__ == "__main__":
    main()

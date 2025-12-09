#!/usr/bin/env python3

import boto3
from utils.regions import list_regions
from collectors.ec2 import collect_ec2_instances
from collectors.ebs import collect_ebs_volumes
from collectors.s3 import collect_s3_buckets
from collectors.asg import collect_auto_scaling_groups
from collectors.lambda_functions import collect_lambda_functions
from output.writer import write_output
from concurrent.futures import ThreadPoolExecutor, as_completed
import argparse
from collectors.asgConverter import collect_asg_as_ec2_equivalent
from utils.spinner import start_spinner, stop_spinner

def parse_args():
    parser = argparse.ArgumentParser(description="Upwind CloudScanner Cost Estimator")

    parser.add_argument("--include-stopped", action="store_true",
                        help="Include stopped EC2 instances")

    parser.add_argument("--include-asg-instances", action="store_true",
                        help="Count individual EC2 inside ASG instead of 1 per ASG")

    parser.add_argument("--include-k8s-asg", action="store_true",
                        help="Do not skip Kubernetes ASGs")

    return parser.parse_args()


def scan_region(region, args):
    session = boto3.Session(region_name=region)

    try:
        return (
            collect_ec2_instances(session, region, args) +
            collect_asg_as_ec2_equivalent(session, region, args) +  # << here
            collect_ebs_volumes(session, region, args) +
            collect_lambda_functions(session, region, args)
        )

    except Exception as e:
        return []



def main():
    print("\n🚀 Upwind CloudScanner Cost Estimator\n")

    sts = boto3.client("sts")
    identity = sts.get_caller_identity()
    print(f"🏢 Account: {identity['Account']}")

    args = parse_args()
    regions = list_regions()
    results = []

    start_spinner()

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(scan_region, r, args) for r in regions]
        for f in as_completed(futures):
            results += f.result()

    stop_spinner()
    print(f"✔ Scan complete — resources collected: {len(results)}\n")

    write_output(results,
                 json_filename="upwind_report.json",
                 csv_filename="upwind_report.csv")

if __name__ == "__main__":
    main()

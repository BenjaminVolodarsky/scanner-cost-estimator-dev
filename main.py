#!/usr/bin/env python3

import boto3
from utils.regions import list_regions
from collectors.ec2 import collect_ec2_instances
from collectors.ebs import collect_ebs_volumes
from collectors.s3 import collect_s3_buckets
from collectors.lambda_functions import collect_lambda_functions
from collectors.asgConverter import collect_asg_as_ec2_equivalent
from output.writer import write_output
from concurrent.futures import ThreadPoolExecutor, as_completed
import argparse
from utils.spinner import start_spinner, stop_spinner

def parse_args():
    parser = argparse.ArgumentParser(description="Upwind CloudScanner Cost Estimator")
    parser.add_argument("--include-stopped", action="store_true")
    parser.add_argument("--include-asg-instances", action="store_true")
    parser.add_argument("--include-k8s-asg", action="store_true")
    return parser.parse_args()



def scan_region(region, args):
    session = boto3.Session(region_name=region)
    region_results = []

    try: region_results += collect_ec2_instances(session, region, args)
    except: pass

    try: region_results += collect_asg_as_ec2_equivalent(session, region, args)
    except: pass

    try: region_results += collect_ebs_volumes(session, region, args)
    except: pass

    try: region_results += collect_lambda_functions(session, region, args)
    except: pass

    return region_results



def main():
    args = parse_args()
    regions = list_regions()
    results = []

    start_spinner()
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(scan_region, r, args) for r in regions]
        for f in as_completed(futures):
            results += f.result()
    stop_spinner()

    results += collect_s3_buckets(boto3.Session())

    print(f"\n✔ Scan complete — total collected Assets: {len(results)}")
    write_output(results,
                 json_filename="upwind_report.json",
                 csv_filename="upwind_report.csv")

    print("\n Output:")
    print("   output/upwind_report.json")
    print("   output/upwind_report.csv\n")


if __name__ == "__main__":
    main()

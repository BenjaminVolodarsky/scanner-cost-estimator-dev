#!/usr/bin/env python3

from collectors.s3 import collect_s3_buckets
from collectors.ec2 import collect_ec2_instances
from collectors.ebs import collect_ebs_volumes
from collectors.asg import collect_auto_scaling_groups
from output.writer import write_output


def main():
    print("\n📡 Collecting Environment Data for Cloudscanner Cost Estimation...\n")

    master = []

    # --- Merge all datasets into one list ---
    master += [{"resource_type": "s3_bucket", **b} for b in collect_s3_buckets()]
    master += [{"resource_type": "ec2_instance", **i} for i in collect_ec2_instances()]
    master += [{"resource_type": "ebs_volume", **v} for v in collect_ebs_volumes()]
    master += [{"resource_type": "asg", **g} for g in collect_auto_scaling_groups()]

    print(f"\nTotal collected assets: {len(master)}\n")

    write_output(master, csv_name="cloudscanner_master_report.csv")


if __name__ == "__main__":
    main()

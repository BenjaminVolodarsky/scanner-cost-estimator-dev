#!/usr/bin/env python3

import json
from collectors.s3 import collect_s3_buckets
from collectors.asg import collect_auto_scaling_groups
from collectors.ebs import collect_ebs_volumes
from collectors.ec2 import collect_ec2_instances
from output.writer import write_output
from collectors.test import collect_asg


def main():
    print("collecting Environment sizing for Cloudscanner Cost Estimation")

    write_output(collect_asg())

if __name__ == "__main__":
    main()
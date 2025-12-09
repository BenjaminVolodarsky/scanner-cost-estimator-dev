# collectors/ec2.py

import boto3

def collect_ec2_instances(session, region, args=None):
    ec2 = session.client("ec2", region_name=region)
    result = []
    skipped_asg = 0
    skipped_stopped = 0

    try:
        paginator = ec2.get_paginator("describe_instances")
        for page in paginator.paginate():
            for reservation in page.get("Reservations", []):
                for inst in reservation.get("Instances", []):

                    state = inst.get("State", {}).get("Name")

                    # Skip stopped instances unless user requests otherwise
                    if state == "stopped" and not args.include_stopped:
                        skipped_stopped += 1
                        continue

                    tags = {t["Key"]: t["Value"] for t in inst.get("Tags", [])}

                    # Skip EC2 inside ASG unless user asks to count individually
                    if "aws:autoscaling:groupName" in tags and not args.include_asg_instances:
                        skipped_asg += 1
                        continue

                    result.append({
                        "resource": "ec2",
                        "region": region,
                        "type": inst.get("InstanceType"),
                        "lifecycle": inst.get("InstanceLifecycle", "on-demand"),
                    })

    except Exception as e:
        # silent fail for customers
        return result

    return result

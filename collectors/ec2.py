import boto3

def collect_ec2_instances(session, region, args=None, debug=False):
    ec2 = session.client("ec2", region_name=region)
    result = []

    try:
        paginator = ec2.get_paginator("describe_instances")
        for page in paginator.paginate():
            for reservation in page.get("Reservations", []):
                for inst in reservation.get("Instances", []):

                    state = inst.get("State", {}).get("Name")
                    tags = {t["Key"]: t["Value"] for t in inst.get("Tags", [])}

                    if state == "stopped" and not args.include_stopped:
                        continue

                    if "aws:autoscaling:groupName" in tags and not args.include_asg_instances:
                        continue

                    result.append({
                        "resource": "ec2",
                        "region": region,
                        "type": inst.get("InstanceType"),
                        "lifecycle": inst.get("InstanceLifecycle", "on-demand"),
                    })

    except Exception as e:
        if debug:
            print(f"⚠️ EC2 scan failed in {region} → {e}")
        return []

    return result

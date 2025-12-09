import boto3

def collect_ec2_instances(session, region, args):
    client = session.client("ec2", region_name=region)
    result = []

    try:
        paginator = client.get_paginator("describe_instances")
        for page in paginator.paginate():
            for reservation in page.get("Reservations", []):
                for inst in reservation.get("Instances", []):

                    state = inst.get("State", {}).get("Name")

                    # skip stopped unless flag
                    if state == "stopped" and not args.include_stopped:
                        continue

                    tags = {t["Key"]: t["Value"] for t in inst.get("Tags", [])}

                    # skip EC2 part of ASG unless flag
                    if "aws:autoscaling:groupName" in tags and not args.include_asg_instances:
                        continue

                    result.append({
                        "resource": "ec2",
                        "region": region,
                        "instance_id": inst.get("InstanceId"),
                        "instance_type": inst.get("InstanceType"),
                        "lifecycle": inst.get("InstanceLifecycle", "on-demand"),
                        "state": state,
                        "private_ip": inst.get("PrivateIpAddress"),
                        "tags": tags
                    })

    except Exception as e:
        print(f"⚠️ EC2 scan failed in {region} → {e}")

    return result

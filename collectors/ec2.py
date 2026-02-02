import boto3

def collect_ec2_instances(session, region, args=None, account_id="unknown"):
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
                        "account_id": account_id,
                        "resource": "ec2",
                        "region": region,
                        "type": inst.get("InstanceType"),
                        "state": state,
                    })
    except Exception as e:
        print(f"⚠️ EC2 error in {account_id} [{region}]: {e}")
        return []
    return result
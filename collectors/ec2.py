import boto3

def collect_ec2_instances(session, region):
    ec2 = session.client("ec2", region_name=region)
    instances = []

    resp = ec2.describe_instances()
    for res in resp['Reservations']:
        for inst in res['Instances']:
            instances.append({
                "type": "ec2",
                "region": region,
                "instance_id": inst.get("InstanceId"),
                "instance_type": inst.get("InstanceType"),
                "lifecycle": inst.get("InstanceLifecycle", "on-demand"),
                "state": inst.get("State", {}).get("Name"),
                "launch_time": inst.get("LaunchTime").isoformat(),
                "private_ip": inst.get("PrivateIpAddress"),
                "public_ip": inst.get("PublicIpAddress"),
                "tags": {t["Key"]: t["Value"] for t in inst.get("Tags", [])}
            })
    return instances

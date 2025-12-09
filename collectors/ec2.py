import boto3
from botocore.exceptions import ClientError


def collect_ec2_instances(session, region):
    ec2 = session.client("ec2", region_name=region)

    try:
        resp = ec2.describe_instances()
    except ClientError as e:
        print(f"⚠️  Skipping region {region} (no access / not enabled) → {e.response['Error']['Code']}")
        return []

    instances = []
    for res in resp.get("Reservations", []):
        for inst in res.get("Instances", []):
            instances.append({
                "type": "ec2",
                "region": region,
                "instance_id": inst.get("InstanceId"),
                "instance_type": inst.get("InstanceType"),
                "lifecycle": inst.get("InstanceLifecycle", "on-demand"),
                "state": inst.get("State", {}).get("Name"),
                "launch_time": inst.get("LaunchTime").isoformat() if inst.get("LaunchTime") else None,
                "private_ip": inst.get("PrivateIpAddress"),
                "public_ip": inst.get("PublicIpAddress"),
                "availability_zone": inst.get("Placement", {}).get("AvailabilityZone"),
                "tags": {t["Key"]: t["Value"] for t in inst.get("Tags", [])}
            })

    return instances

import boto3

def collect_ec2_instances():
    ec2 = boto3.client("ec2")
    response = ec2.describe_instances()

    instances = []
    for reservation in response.get("Reservations", []):
        for instance in reservation.get("Instances", []):
            instances.append({
                "instance_id": instance.get("InstanceId"),
                "instance_type": instance.get("InstanceType"),
                "region": ec2.meta.region_name,
                "state": instance.get("State", {}).get("Name"),
                "launch_time": instance.get("LaunchTime").isoformat() if instance.get("LaunchTime") else None,
            })

    return instances

import boto3

def collect_ec2_test():
    ec2 = boto3.client("ec2", region_name="us-east-1")

    response = ec2.describe_instances()

    instances = []
    for reservation in response.get("Reservations", []):
        for inst in reservation.get("Instances", []):
            instances.append({
                "instance_id": inst.get("InstanceId"),
                "instance_type": inst.get("InstanceType"),
                "lifecycle": inst.get("InstanceLifecycle", "on-demand"),  # spot or on-demand
                "state": inst.get("State", {}).get("Name"),
                "launch_time": inst.get("LaunchTime").isoformat(),
                "private_ip": inst.get("PrivateIpAddress"),
                "public_ip": inst.get("PublicIpAddress"),
                "availability_zone": inst.get("Placement", {}).get("AvailabilityZone"),
                "tags": {t["Key"]: t["Value"] for t in inst.get("Tags", [])}
            })

    print(f"Found {len(instances)} instances:")
    for i in instances:
        print(i)

    return instances

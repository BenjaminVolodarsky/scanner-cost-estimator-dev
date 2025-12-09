import boto3

def collect_ebs_volumes():
    ec2 = boto3.client("ec2")
    response = ec2.describe_volumes()

    volumes = []
    for vol in response.get("Volumes", []):
        volumes.append({
            "volume_id": vol.get("VolumeId"),
            "size_gb": vol.get("Size"),
            "type": vol.get("VolumeType"),
            "iops": vol.get("Iops"),
            "state": vol.get("State"),
            "region": ec2.meta.region_name,
        })

    print(volumes)

    return volumes

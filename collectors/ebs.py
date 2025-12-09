import boto3
from utils.safe_call import safe_aws_call

def collect_ebs_volumes(session, region, args=None):
    ec2 = session.client("ec2", region_name=region)

    resp = safe_aws_call(lambda: ec2.describe_volumes(), region)
    if not resp:
        return []

    volumes = []
    for v in resp.get("Volumes", []):
        volumes.append({
            "type": "ebs",
            "region": region,
            "volume_id": v.get("VolumeId"),
            "size_gb": v.get("Size"),
            "type": v.get("VolumeType"),
            "iops": v.get("Iops"),
            "state": v.get("State"),
        })

    return volumes

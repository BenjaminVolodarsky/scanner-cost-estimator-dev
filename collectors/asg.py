import boto3
from utils.safe_call import safe_aws_call

def collect_auto_scaling_groups(session, region):
    asg = session.client("autoscaling", region_name=region)

    resp = safe_aws_call(lambda: asg.describe_auto_scaling_groups(), region)
    if not resp:
        return []

    groups = []
    for g in resp.get("AutoScalingGroups", []):
        groups.append({
            "type": "asg",
            "region": region,
            "name": g.get("AutoScalingGroupName"),
            "desired": g.get("DesiredCapacity"),
            "min": g.get("MinSize"),
            "max": g.get("MaxSize"),
            "instances": [i.get("InstanceId") for i in g.get("Instances", [])],
            "tags": {t["Key"]: t["Value"] for t in g.get("Tags", [])},
        })

    return groups

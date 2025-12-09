import boto3

def collect_auto_scaling_groups():
    asg = boto3.client("autoscaling")
    response = asg.describe_auto_scaling_groups()

    groups = []
    for group in response.get("AutoScalingGroups", []):
        groups.append({
            "name": group.get("AutoScalingGroupName"),
            "desired_capacity": group.get("DesiredCapacity"),
            "min_size": group.get("MinSize"),
            "max_size": group.get("MaxSize"),
            "instances": len(group.get("Instances", [])),
        })

    return groups

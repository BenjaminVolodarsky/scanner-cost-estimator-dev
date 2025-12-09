import boto3

def collect_asg():
    asg = boto3.client("autoscaling")

    response = asg.describe_auto_scaling_groups()

    groups = []
    for group in response["AutoScalingGroups"]:
        groups.append({
            "name": group["AutoScalingGroupName"],
            "desired": group["DesiredCapacity"],
            "min": group["MinSize"],
            "max": group["MaxSize"],
            "instances": [i["InstanceId"] for i in group["Instances"]],
            "launch_template": group.get("LaunchTemplate", {}),
            "tags": {t["Key"]: t["Value"] for t in group.get("Tags", [])},
        })

        print(groups)

    return groups

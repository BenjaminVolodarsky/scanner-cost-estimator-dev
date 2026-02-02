# Inside collectors/asgConverter.py

def collect_asg_as_ec2_equivalent(session, region, account_id):
    client = session.client("autoscaling", region_name=region)
    results = []
    error = None
    try:
        paginator = client.get_paginator('describe_auto_scaling_groups')
        for page in paginator.paginate():
            for asg in page['AutoScalingGroups']:
                tags = {t["Key"]: t["Value"] for t in asg.get("Tags", [])}

                # Exclude if it's a K8s cluster
                is_k8s = any(x in str(tags).lower() for x in ["eks", "k8", "kubernetes"])
                if is_k8s:
                    continue

                # Exclude if the ASG is empty
                if asg.get("DesiredCapacity", 0) == 0:
                    continue

                results.append({
                    "account_id": account_id,
                    "resource": "asg_ec2_equivalent",
                    "region": region,
                    "name": asg['AutoScalingGroupName'],
                    "instance_count": len(asg['Instances'])
                })
    except Exception as e:
        if "AccessDenied" in str(e):
            error = "autoscaling:DescribeAutoScalingGroups"
        return results, error
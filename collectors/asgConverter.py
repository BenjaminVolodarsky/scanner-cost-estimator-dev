import boto3

# simple ASG → ec2-like lightweight output

def collect_asg_as_ec2_equivalent(session, region, args=None):
    client = session.client("autoscaling", region_name=region)
    results = []

    try:
        paginator = client.get_paginator("describe_auto_scaling_groups")
        for page in paginator.paginate():
            for asg in page.get("AutoScalingGroups", []):

                tags = {t["Key"]: t["Value"] for t in asg.get("Tags", [])}

                # Skip Kubernetes nodegroups unless user flag enables them
                is_k8s = any(x in str(tags) for x in ["eks", "k8", "kubernetes"])
                if is_k8s and not args.include_k8s_asg:
                    continue

                # default count = 1 scanning unit per ASG
                size = asg.get("DesiredCapacity", 1)

                results.append({
                    "resource": "ec2",       # customer sees it like scan unit
                    "region": region,
                    "type": "asg",
                    "lifecycle": f"asg({size})"
                })

    except:
        return []

    return results

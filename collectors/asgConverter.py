import boto3


def collect_asg_as_ec2_equivalent(session, region, args=None, account_id="unknown"):
    client = session.client("autoscaling", region_name=region)
    results = []

    try:
        paginator = client.get_paginator("describe_auto_scaling_groups")
        for page in paginator.paginate():
            for asg in page.get("AutoScalingGroups", []):

                # Convert tags list to a searchable dict
                tags = {t["Key"]: t["Value"] for t in asg.get("Tags", [])}

                # Check for K8s/EKS tags to exclude clusters
                is_k8s = any(x in str(tags).lower() for x in ["eks", "k8", "kubernetes"])

                # Check if the user specifically asked to include K8s
                include_k8s = getattr(args, 'include_k8s_asg', False)

                if is_k8s and not include_k8s:
                    continue

                # Count the ASG as 1x VM target
                results.append({
                    "account_id": account_id,
                    "resource": "ec2",
                    "region": region,
                    "type": "asg_target",
                    "lifecycle": "asg",
                    "asg_name": asg.get("AutoScalingGroupName")
                })

    except Exception:
        return []

    return results
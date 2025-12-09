import boto3

# tags used to detect Kubernetes
K8S_TAG_KEYS = [
    "kubernetes.io/cluster/",
    "k8s.io/cluster-autoscaler/enabled",
    "eks:cluster-name",
    "alpha.eksctl.io/nodegroup-name"
]


def is_kubernetes_asg(tags: dict) -> bool:
    for key in tags.keys():
        if any(k in key for k in K8S_TAG_KEYS):
            return True
    return False


def collect_auto_scaling_groups(session, region, args=None):
    client = session.client("autoscaling", region_name=region)
    results = []

    try:
        paginator = client.get_paginator("describe_auto_scaling_groups")
        for page in paginator.paginate():
            for asg in page["AutoScalingGroups"]:

                tags = {t["Key"]: t["Value"] for t in asg.get("Tags", [])}
                is_k8s = is_kubernetes_asg(tags)

                # skip Kubernetes ASG unless flag overrides
                if is_k8s and not args.include_k8s_asg:
                    continue

                results.append({
                    "resource": "asg",
                    "region": region,
                    "name": asg["AutoScalingGroupName"],
                    "desired": asg["DesiredCapacity"],
                    "counted_as": 1 if not args.include_asg_instances else asg["DesiredCapacity"],
                    "tags": tags,
                    "kubernetes_detected": is_k8s
                })

    except Exception as e:
        print(f"⚠️ ASG scan failed in {region} → {e}")

    return results

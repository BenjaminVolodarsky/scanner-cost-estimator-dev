def collect_asg_as_ec2_equivalent(session, region, account_id):
    client = session.client("autoscaling", region_name=region)
    results = []
    error = None
    try:
        paginator = client.get_paginator('describe_auto_scaling_groups')
        for page in paginator.paginate():
            for asg in page['AutoScalingGroups']:
                if asg.get('DesiredCapacity') == 0:
                    continue

                results.append({
                    "account_id": account_id,
                    "resource": "asg_ec2_equivalent",
                    "region": region,
                    "asg_name": asg['AutoScalingGroupName'],
                    "asg_instance_count": len(asg['Instances'])
                })
    except Exception as e:
        if "AccessDenied" in str(e):
            error = "autoscaling:DescribeAutoScalingGroups"
    return results, error
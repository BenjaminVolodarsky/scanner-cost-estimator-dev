from botocore.exceptions import ClientError


def collect_ec2_instances(session, region, account_id):
    client = session.client("ec2", region_name=region)
    results = []
    error = None
    try:
        paginator = client.get_paginator('describe_instances')
        for page in paginator.paginate():
            for reservation in page['Reservations']:
                for instance in reservation['Instances']:
                    # Filter K8s if needed
                    tags = {t['Key']: t['Value'] for t in instance.get('Tags', [])}
                    if any(k in str(tags).lower() for k in ['eks', 'k8s', 'kubernetes']):
                        continue

                    results.append({
                        "account_id": account_id,
                        "resource": "ec2",
                        "region": region,
                        "id": instance['InstanceId'],
                        "type": instance['InstanceType'],
                        "state": instance['State']['Name']
                    })
    except Exception as e:
        if "AccessDenied" in str(e) or "UnauthorizedOperation" in str(e):
            error = "ec2:DescribeInstances"
    return results, error
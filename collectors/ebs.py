def collect_ebs_volumes(session, region, account_id):
    client = session.client("ec2", region_name=region)
    results = []
    error = None
    try:
        paginator = client.get_paginator('describe_volumes')
        for page in paginator.paginate():
            for vol in page['Volumes']:
                results.append({
                    "account_id": account_id,
                    "resource": "ebs",
                    "region": region,
                    "id": vol['VolumeId'],
                    "size_gb": vol['Size'],
                    "type": vol['VolumeType']
                })
    except Exception as e:
        if "AccessDenied" in str(e) or "UnauthorizedOperation" in str(e):
            error = "ec2:DescribeVolumes"
    return results, error

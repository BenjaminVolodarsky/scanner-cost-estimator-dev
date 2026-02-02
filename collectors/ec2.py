import boto3

def collect_ec2_instances(session, region, args=None, account_id="unknown"):
    ec2 = session.client("ec2", region_name=region)
    result = []

    try:
        paginator = ec2.get_paginator("describe_instances")
        for page in paginator.paginate():
            for reservation in response.get('Reservations', []):
                for instance in reservation.get('Instances', []):
                    try:
                        # Check for K8s/EKS tags to exclude them
                        tags = {t['Key']: t['Value'] for t in instance.get('Tags', [])}
                        is_k8s = any(k in str(tags).lower() for k in ['eks', 'k8s', 'kubernetes'])

                        if is_k8s:
                            continue

                        # SUCCESS: Append the instance data
                        results.append({
                            "account_id": account_id,
                            "resource": "ec2",
                            "instance_id": instance['InstanceId'],
                            "type": instance['InstanceType'],
                            "region": region,
                            "state": instance['State']['Name']
                        })
                    except Exception as e:
                        print(f"⚠️ Error processing instance {instance.get('InstanceId')}: {e}")
    except Exception as e:
        print(f"⚠️ EC2 error in {account_id} [{region}]: {e}")
        return []
    return result
import boto3


def collect_ec2_instances(session, region, account_id="unknown"):
    client = session.client("ec2", region_name=region)
    results = []

    try:
        # 🚀 ADD THIS LINE TO DEFINE 'response'
        response = client.describe_instances()

        for reservation in response.get('Reservations', []):
            for instance in reservation.get('Instances', []):
                # Check for K8s/EKS tags to exclude them
                tags = {t['Key']: t['Value'] for t in instance.get('Tags', [])}
                is_k8s = any(k in str(tags).lower() for k in ['eks', 'k8s', 'kubernetes'])

                if is_k8s:
                    continue

                results.append({
                    "account_id": account_id,
                    "resource": "ec2",
                    "instance_id": instance['InstanceId'],
                    "type": instance['InstanceType'],
                    "region": region,
                    "state": instance['State']['Name']
                })
    except Exception as e:
        print(f"⚠️ EC2 error in {account_id} [{region}]: {e}")

    return results
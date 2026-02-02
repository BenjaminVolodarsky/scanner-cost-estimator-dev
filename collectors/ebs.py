# collectors/ebs.py
from botocore.exceptions import ClientError


def collect_ebs_volumes(session, region, account_id="unknown"):
    client = session.client("ec2", region_name=region)
    results = []
    try:
        response = client.describe_volumes()
        for vol in response.get('Volumes', []):
            results.append({
                "account_id": account_id,
                "resource": "ebs",
                "volume_id": vol['VolumeId'],
                "region": region,
                "size_gb": vol['Size'],
                "state": vol['State']
            })
    except Exception:
        # Silently fail on permission/auth errors to keep logs clean
        pass
    return results
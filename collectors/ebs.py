def collect_ebs_volumes(session, region, args=None, account_id="unknown"):
    ec2 = session.client("ec2", region_name=region)
    volumes = []

    try:
        resp = ec2.describe_volumes()
        for v in resp.get("Volumes", []):
            volumes.append({
                "account_id": account_id,
                "resource": "ebs",
                "region": region,
                "size_gb": v.get("Size"),
                "type": v.get("VolumeType"),
            })
    except:
        return []
    return volumes
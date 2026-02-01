def collect_s3_buckets(session, account_id="unknown"):
    s3 = session.client("s3")
    results = []

    try:
        buckets = s3.list_buckets()["Buckets"]
        for bucket in buckets:
            name = bucket["Name"]
            # Location check can be slow; for POC, us-east-1 is often the default
            try:
                loc = s3.get_bucket_location(Bucket=name)["LocationConstraint"] or "us-east-1"
            except:
                loc = "unknown"

            results.append({
                "account_id": account_id,
                "resource": "s3_bucket",
                "bucket_name": name,
                "region": loc,
            })
    except:
        return []
    return results
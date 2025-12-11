import boto3
from datetime import datetime, timedelta

def collect_s3_buckets(session, region=None, args=None):

    s3 = session.client("s3")

    try:
        buckets = s3.list_buckets()["Buckets"]
    except Exception as e:
        return []

    results = []

    for bucket in buckets:
        name = bucket["Name"]
        creation = bucket["CreationDate"].isoformat()

        # bucket region lookup
        try:
            loc = s3.get_bucket_location(Bucket=name)["LocationConstraint"] or "us-east-1"
        except:
            loc = "unknown"

        results.append({
            "resource": "s3_bucket",
            "region": loc,
        })

    return results

# collectors/s3.py

import boto3
from datetime import datetime, timedelta

def collect_s3_buckets(session, region=None):
    """List buckets + retrieve size via CloudWatch metrics."""

    s3 = session.client("s3")
    cw = session.client("cloudwatch")

    results = []

    try:
        buckets = s3.list_buckets()["Buckets"]
    except Exception as e:
        print(f"   ⚠️ S3 access denied in {region} → {e}")
        return []

    for bucket in buckets:
        name = bucket["Name"]
        creation = bucket["CreationDate"].isoformat()

        # Get bucket location (required for region mapping)
        try:
            loc = s3.get_bucket_location(Bucket=name)["LocationConstraint"] or "us-east-1"
        except:
            loc = "unknown"

        # Retrieve storage metrics
        try:
            metrics = cw.get_metric_statistics(
                Namespace="AWS/S3",
                MetricName="BucketSizeBytes",
                Dimensions=[
                    {"Name": "BucketName", "Value": name},
                    {"Name": "StorageType", "Value": "StandardStorage"} # could add Glacier/Tiers later
                ],
                StartTime=datetime.utcnow() - timedelta(days=2),
                EndTime=datetime.utcnow(),
                Period=86400,
                Statistics=["Average"]
            )

            size_bytes = metrics["Datapoints"][0]["Average"] if metrics["Datapoints"] else 0
            size_gb = round(size_bytes / 1024 / 1024 / 1024, 2)

        except Exception as e:
            size_gb = None
            print(f"   ⚠️ Failed to fetch size for {name} → {e}")

        results.append({
            "resource": "s3_bucket",
            "bucket_name": name,
            "region": loc,
            "creation_date": creation,
            "size_gb": size_gb
        })

    return results

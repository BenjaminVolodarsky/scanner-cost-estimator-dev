import boto3
from datetime import datetime, timedelta

def collect_s3_buckets(session, region=None, args=None):

    s3 = session.client("s3")
    cw = session.client("cloudwatch")

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

        # fetch size (optional)
        try:
            metrics = cw.get_metric_statistics(
                Namespace="AWS/S3",
                MetricName="BucketSizeBytes",
                Dimensions=[{"Name": "BucketName", "Value": name},
                            {"Name": "StorageType", "Value": "StandardStorage"}],
                StartTime=datetime.utcnow() - timedelta(days=2),
                EndTime=datetime.utcnow(),
                Period=86400,
                Statistics=["Average"]
            )
            size_gb = round(metrics["Datapoints"][0]["Average"] / 1024**3, 2) if metrics["Datapoints"] else 0.0
        except:
            size_gb = 0.0

        results.append({
            "resource": "s3_bucket",
            "region": loc,
            "size_gb": size_gb
        })

    return results

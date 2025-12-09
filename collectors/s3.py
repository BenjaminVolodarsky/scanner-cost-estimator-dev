import boto3
from datetime import datetime, timedelta

def get_bucket_size_bytes(bucket_name, region):
    cloudwatch = boto3.client("cloudwatch", region_name=region)

    # Most recent metric datapoint (AWS updates daily)
    metric = cloudwatch.get_metric_statistics(
        Namespace="AWS/S3",
        MetricName="BucketSizeBytes",
        Dimensions=[
            {"Name": "BucketName", "Value": bucket_name},
            {"Name": "StorageType", "Value": "StandardStorage"}  # cost-bearing storage
        ],
        StartTime=datetime.utcnow() - timedelta(days=3),
        EndTime=datetime.utcnow(),
        Period=86400,                   # 1 day
        Statistics=["Average"]          # AWS stores one per day, avg is fine
    )

    datapoints = metric.get("Datapoints", [])
    if not datapoints:
        return 0  # No metrics yet

    return int(datapoints[-1]["Average"])   # Latest value


def collect_s3_buckets():
    s3 = boto3.client("s3")
    response = s3.list_buckets()

    buckets = []

    for bucket in response["Buckets"]:
        name = bucket["Name"]

        # Determine bucket region
        region_resp = s3.get_bucket_location(Bucket=name)
        region = region_resp.get("LocationConstraint") or "us-east-1"

        # Fetch bucket size from CloudWatch
        size_bytes = get_bucket_size_bytes(name, region)
        size_gb = round(size_bytes / (1024**3), 3)

        buckets.append({
            "bucket_name": name,
            "region": region,
            "created_at": bucket["CreationDate"].isoformat(),
            "size_bytes": size_bytes,
            "size_gb": size_gb
        })

    print("S3 Buckets discovered:", buckets)
    return buckets

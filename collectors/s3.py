import boto3
from datetime import datetime, timedelta


def collect_s3_buckets(session, account_id="unknown"):
    s3 = session.client("s3")
    # CloudWatch metrics for S3 are stored in us-east-1
    cw = session.client("cloudwatch", region_name="us-east-1")
    results = []
    error = None

    try:
        buckets = s3.list_buckets().get("Buckets", [])
        now = datetime.utcnow()

        for bucket in buckets:
            name = bucket["Name"]

            # 1. Get Bucket Location
            try:
                loc = s3.get_bucket_location(Bucket=name).get("LocationConstraint") or "us-east-1"
            except:
                loc = "unknown"

            # 2. Query CloudWatch for Bucket Size
            # We look back 2 days to ensure we find a daily metric point
            size_gb = 0
            try:
                size = cw.get_metric_statistics(
                    Namespace='AWS/S3',
                    MetricName='BucketSizeBytes',
                    Dimensions=[
                        {'Name': 'BucketName', 'Value': name},
                        {'Name': 'StorageType', 'Value': 'StandardStorage'}
                    ],
                    Statistics=['Average'],
                    Period=86400,  # 24 hours in seconds
                    StartTime=now - timedelta(days=2),
                    EndTime=now
                )

                if size['Datapoints']:
                    # Convert Bytes to GB
                    bytes_val = size['Datapoints'][0]['Average']
                    size_gb = round(bytes_val / (1024 ** 3), 2)
            except:
                pass  # Default to 0 if metrics are inaccessible

            doc_num_val = 0  # Initialize with a default value
            try:
                response = cw.get_metric_statistics(
                    Namespace='AWS/S3',
                    MetricName='NumberOfObjects',
                    Dimensions=[
                        {'Name': 'BucketName', 'Value': name},
                        {'Name': 'StorageType', 'Value': 'AllStorageTypes'}
                    ],
                    Statistics=['Average'],
                    Period=86400,
                    StartTime=now - timedelta(days=2),
                    EndTime=now
                )

                if response.get('Datapoints'):
                    # Sort by timestamp to get the most recent point if multiple exist
                    sorted_datapoints = sorted(response['Datapoints'], key=lambda x: x['Timestamp'], reverse=True)
                    doc_num_val = int(sorted_datapoints[0]['Average'])
            except Exception as e:
                print(f"⚠️ Could not get object count for {name}: {e}")

            results.append({
                "account_id": account_id,
                "resource": "s3_bucket",
                "bucket_name": name,
                "region": loc,
                "size_gb": size_gb,
                "doc_num": doc_num_val  # Use the validated variable
            })
    except Exception as e:
        if "AccessDenied" in str(e):
            error = "s3:ListBuckets"
    return results, error
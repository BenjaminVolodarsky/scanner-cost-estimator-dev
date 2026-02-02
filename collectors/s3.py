from datetime import datetime, timedelta


def collect_s3_buckets(session, account_id="unknown"):
    s3 = session.client("s3")
    cw = session.client("cloudwatch", region_name="us-east-1")
    results = []
    error = None

    try:
        buckets = s3.list_buckets().get("Buckets", [])
        now = datetime.utcnow()

        for bucket in buckets:
            name = bucket["Name"]

            try:
                loc = s3.get_bucket_location(Bucket=name).get("LocationConstraint") or "us-east-1"
            except:
                loc = "unknown"

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
                    Period=86400,
                    StartTime=now - timedelta(days=2),
                    EndTime=now
                )

                if size['Datapoints']:
                    bytes_val = size['Datapoints'][0]['Average']
                    size_gb = round(bytes_val / (1024 ** 3), 2)
            except:
                pass

            doc_num_val = 0
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
                "doc_num": doc_num_val
            })
    except Exception as e:
        if "AccessDenied" in str(e):
            error = "s3:ListBuckets"
    return results, error
from datetime import datetime, timedelta
from utils.config_helper import get_client


def collect_s3_buckets(session, account_id="unknown"):
    """
    Collects S3 bucket metadata and metrics using high-performance batching.
    """
    s3 = get_client(session, "s3")
    results = []
    error = None

    # Bucket grouping to batch CloudWatch calls by region
    buckets_by_region = {}

    try:
        # 1. Get list of all buckets in the account
        all_buckets = s3.list_buckets().get("Buckets", [])
        now = datetime.utcnow()
        start_time = now - timedelta(days=2)

        # 2. Discover regions for all buckets
        for b in all_buckets:
            name = b["Name"]
            try:
                # head_bucket is faster and more reliable than get_bucket_location
                region = s3.head_bucket(Bucket=name).get('ResponseMetadata', {}).get('HTTPHeaders', {}).get(
                    'x-amz-bucket-region', 'us-east-1')
            except:
                region = 'us-east-1'

            if region not in buckets_by_region:
                buckets_by_region[region] = []
            buckets_by_region[region].append(name)

        # 3. Batch fetch metrics per region using GetMetricData
        for region, bucket_names in buckets_by_region.items():
            cw = get_client(session, "cloudwatch", region_name=region)

            # Each GetMetricData call supports up to 500 queries
            # Since we fetch 2 metrics per bucket (Size and Count), we chunk at 250 buckets

            chunk_size = 250
            for i in range(0, len(bucket_names), chunk_size):
                chunk = bucket_names[i:i + chunk_size]

                queries = []
                for idx, b_name in enumerate(chunk):
                    # Query for Bucket Size
                    queries.append({
                        'Id': f'size_{idx}',
                        'MetricStat': {
                            'Metric': {
                                'Namespace': 'AWS/S3',
                                'MetricName': 'BucketSizeBytes',
                                'Dimensions': [
                                    {'Name': 'BucketName', 'Value': b_name},
                                    {'Name': 'StorageType', 'Value': 'StandardStorage'}
                                ]
                            },
                            'Period': 86400,
                            'Stat': 'Average'
                        },
                        'Label': f"{b_name}|size"
                    })
                    queries.append({
                        'Id': f'count_{idx}',
                        'MetricStat': {
                            'Metric': {
                                'Namespace': 'AWS/S3',
                                'MetricName': 'NumberOfObjects',
                                'Dimensions': [
                                    {'Name': 'BucketName', 'Value': b_name},
                                    {'Name': 'StorageType', 'Value': 'AllStorageTypes'}
                                ]
                            },
                            'Period': 86400,
                            'Stat': 'Average'
                        },
                        'Label': f"{b_name}|count"
                    })

                try:
                    # Single network call for up to 250 buckets!
                    response = cw.get_metric_data(
                        MetricDataQueries=queries,
                        StartTime=start_time,
                        EndTime=now
                    )

                    # Organize responses into a map for easy lookup
                    metrics_map = {res['Label']: (res['Values'][0] if res['Values'] else 0) for res in
                                   response['MetricDataResults']}

                    for b_name in chunk:
                        size_val = metrics_map.get(f"{b_name}|size", 0)
                        count_val = metrics_map.get(f"{b_name}|count", 0)

                        results.append({
                            "account_id": account_id,
                            "resource": "s3_bucket",
                            "bucket_name": b_name,
                            "region": region,
                            "bucket_size_gb": round(size_val / (1024 ** 3), 2),
                            "bucket_doc_num": int(count_val)
                        })
                except Exception:
                    # Fallback: if CloudWatch fails for this batch, record buckets with 0
                    for b_name in chunk:
                        results.append({
                            "account_id": account_id,
                            "resource": "s3_bucket",
                            "bucket_name": b_name,
                            "region": region,
                            "bucket_size_gb": 0,
                            "bucket_doc_num": 0
                        })

    except Exception as e:
        if "AccessDenied" in str(e):
            error = "s3:ListBuckets"
        else:
            error = str(e)

    return results, error
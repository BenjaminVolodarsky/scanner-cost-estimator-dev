from datetime import datetime, timedelta


def collect_s3_buckets(session, account_id="unknown"):
    s3 = session.client("s3")
    results = []
    error = None

    cw_clients = {}

    try:
        buckets = s3.list_buckets().get("Buckets", [])
        now = datetime.utcnow()

        for bucket in buckets:
            name = bucket["Name"]

            try:
                loc_resp = s3.get_bucket_location(Bucket=name)
                region = loc_resp['LocationConstraint'] or 'us-east-1'
                if region == 'EU':
                    region = 'eu-west-1'
            except:
                region = 'us-east-1'

            if region not in cw_clients:
                try:
                    cw_clients[region] = session.client("cloudwatch", region_name=region)
                except Exception:
                    cw_clients[region] = None

            cw = cw_clients.get(region)

            size_gb = 0
            if cw:
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
                        bytes_val = sorted(size['Datapoints'], key=lambda x: x['Timestamp'])[-1]['Average']
                        size_gb = round(bytes_val / (1024 ** 3), 2)
                except:
                    pass

            doc_num_val = 0
            if cw:
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
                        latest = sorted(response['Datapoints'], key=lambda x: x['Timestamp'])[-1]
                        doc_num_val = int(latest['Average'])
                except:
                    pass

            results.append({
                "account_id": account_id,
                "resource": "s3_bucket",
                "bucket_name": name,
                "region": region,
                "bucket_size_gb": size_gb,
                "bucket_doc_num": doc_num_val
            })

    except Exception as e:
        if "AccessDenied" in str(e):
            error = "s3:ListBuckets"

    return results, error
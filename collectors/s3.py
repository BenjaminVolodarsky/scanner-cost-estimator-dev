import boto3
from utils.safe_call import safe_aws_call

def collect_s3_buckets(session, region):
    s3 = session.client("s3", region_name=region)

    resp = safe_aws_call(lambda: s3.list_buckets(), region)
    if not resp:
        return []

    buckets = []
    for b in resp.get("Buckets", []):
        name = b["Name"]

        # Try to fetch bucket location
        loc_resp = safe_aws_call(lambda: s3.get_bucket_location(Bucket=name), region)
        bucket_region = (loc_resp.get("LocationConstraint") or "us-east-1") if loc_resp else "unknown"

        # Try fetch bucket size — requires per-bucket iteration
        size_bytes = 0
        if bucket_region == region:     # Only scan if belongs to region scanned
            try:
                s3_regional = session.client("s3", region_name=bucket_region)
                paginator = s3_regional.get_paginator("list_objects_v2")

                for page in paginator.paginate(Bucket=name):
                    for obj in page.get("Contents", []):
                        size_bytes += obj.get("Size", 0)
            except Exception:
                size_bytes = None  # no access / no objects / region mismatch

        buckets.append({
            "type": "s3",
            "bucket": name,
            "region": bucket_region,
            "size_gb": round(size_bytes / 1024**3, 3) if size_bytes else 0,
        })

    return buckets

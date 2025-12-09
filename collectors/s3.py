import boto3
from utils.safe_call import safe_aws_call

def collect_s3_buckets(session):
    s3 = session.client("s3")

    resp = safe_aws_call(lambda: s3.list_buckets(), "global-s3")
    if not resp:
        return []

    buckets = []
    for b in resp.get("Buckets", []):
        name = b["Name"]

        # get region
        loc = safe_aws_call(lambda: s3.get_bucket_location(Bucket=name), "global-s3")
        region = (loc.get("LocationConstraint") or "us-east-1") if loc else "unknown"

        # Estimate size — count objects + sum size (limited to first 10k to avoid freeze)
        size_bytes = 0
        object_count = 0

        try:
            s3_regional = session.client("s3", region_name=region)
            paginator = s3_regional.get_paginator("list_objects_v2")

            for page in paginator.paginate(Bucket=name, PaginationConfig={"MaxItems": 10000}):
                for obj in page.get("Contents", []):
                    size_bytes += obj["Size"]
                    object_count += 1

        except Exception:
            size_bytes = None

        buckets.append({
            "type": "s3",
            "bucket": name,
            "region": region,
            "object_count_sampled": object_count,
            "estimated_size_gb": round((size_bytes or 0) / 1024**3, 2)
        })

    return buckets

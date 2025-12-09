import boto3

def collect_s3_buckets(session, region=None):
    # S3 is global — region parameter not required
    s3 = session.client('s3')

    result = []
    buckets = s3.list_buckets().get('Buckets', [])

    print(f"📦 Found {len(buckets)} buckets")

    for b in buckets:
        name = b["Name"]

        # Try to detect region for bucket
        try:
            loc = s3.get_bucket_location(Bucket=name).get("LocationConstraint") or "us-east-1"
        except:
            loc = "unknown"

        # 🔥 Calculate total bucket size by iterating objects
        total_bytes = 0
        count = 0
        try:
            paginator = s3.get_paginator('list_objects_v2')
            for page in paginator.paginate(Bucket=name):
                for obj in page.get("Contents", []):
                    total_bytes += obj["Size"]
                    count += 1
        except:
            pass  # skip AccessDenied buckets

        result.append({
            "bucket": name,
            "region": loc,
            "total_gb": round(total_bytes / 1024**3, 2),
            "objects": count
        })

    return result

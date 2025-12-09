import boto3
from botocore.exceptions import ClientError

def collect_s3_buckets(session, region):
    """Return list of S3 buckets tagged to the region (metadata only — size later)."""

    s3 = session.client("s3")
    results = []

    try:
        buckets = s3.list_buckets()["Buckets"]
    except ClientError as e:
        print(f"   ⚠️ S3 access denied in {region} → {e}")
        return []

    for b in buckets:
        name = b.get("Name")
        try:
            # We check which region the bucket belongs to
            loc = s3.get_bucket_location(Bucket=name)
            bucket_region = loc.get("LocationConstraint") or "us-east-1"

            if bucket_region != region:
                continue

            results.append({
                "resource": "s3_bucket",
                "bucket_name": name,
                "region": bucket_region,
                "creation_date": b.get("CreationDate").isoformat(),
            })

        except Exception:
            continue

    return results

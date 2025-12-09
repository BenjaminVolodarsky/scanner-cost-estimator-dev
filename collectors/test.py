import boto3

def collect_asg():
    s3 = boto3.client("s3")

    response = s3.list_buckets()

    buckets = []
    for bucket in response["Buckets"]:
        bucket_name = bucket["Name"]

        # Get bucket region
        region_resp = s3.get_bucket_location(Bucket=bucket_name)
        region = region_resp.get("LocationConstraint") or "us-east-1"

        buckets.append({
            "bucket_name": bucket_name,
            "creation_date": bucket["CreationDate"].isoformat(),
            "region": region
        })

    print("Found buckets:", buckets)
    return buckets
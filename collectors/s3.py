import boto3

def collect_s3_buckets():
    s3 = boto3.client("s3")
    response = s3.list_buckets()

    return [{
        "name": bucket["Name"],
        "creation_date": bucket.get("CreationDate").isoformat() if bucket.get("CreationDate") else None
    } for bucket in response.get("Buckets", [])]

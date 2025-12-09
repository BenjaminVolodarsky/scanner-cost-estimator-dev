import boto3

def list_regions():
    ec2 = boto3.client("ec2", region_name="us-east-1")
    response = ec2.describe_regions(AllRegions=True)
    return [r["RegionName"] for r in response["Regions"]]
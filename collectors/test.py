import boto3


def collect_ec2_test():
    ec2 = boto3.client("ec2", region_name="us-east-1")  # ensure region is set

    response = ec2.describe_regions()

    regions = [r['RegionName'] for r in response['Regions']]

    print("Regions discovered:", regions)

    # Return data in clean format
    return {
        "regions": regions,
        "raw": response  # optional, remove later if not needed
    }

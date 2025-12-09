import boto3


def collect_ec2_test():
    ec2 = boto3.client("ec2", region_name="us-east-1")  # ensure region is set

    response = ec2.describe_instances()

    # regions = [r['RegionName'] for r in response['Regions']]

    print("Regions discovered:", response)

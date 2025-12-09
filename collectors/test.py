import boto3

def collect_ec2_test():
    ec2 = boto3.client("ec2")
    response = ec2.describe_regions()
    print('Regions:', response['Regions'])

    return response


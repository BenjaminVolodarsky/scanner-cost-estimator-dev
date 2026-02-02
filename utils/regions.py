import boto3

def list_regions(session=None):
    client = session.client('ec2', region_name='us-east-1') if session else boto3.client('ec2')
    # Use Filters to only get regions that are 'opted-in' or 'built-in'
    regions = client.describe_regions(
        AllRegions=False,
        Filters=[{'Name': 'endpoint-attribute-name', 'Values': ['opt-in-status']},
                 {'Name': 'endpoint-attribute-value', 'Values': ['opt-in-not-required', 'opted-in']}]
    )
    return [r['RegionName'] for r in regions['Regions']]
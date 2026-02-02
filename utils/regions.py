import boto3


def list_regions(session=None):
    # Use the provided session to avoid AuthFailure in management accounts
    client = session.client('ec2', region_name='us-east-1') if session else boto3.client('ec2')

    # Use the correct filter name: 'opt-in-status'
    try:
        response = client.describe_regions(
            AllRegions=False,  # Only get regions that could be enabled
            Filters=[{
                'Name': 'opt-in-status',
                'Values': ['opt-in-not-required', 'opted-in']
            }]
        )
        return [r['RegionName'] for r in response['Regions']]
    except Exception as e:
        # Fallback to standard regions if the filter fails
        return ['us-east-1', 'us-east-2', 'us-west-1', 'us-west-2', 'eu-central-1']
from botocore.exceptions import ClientError, EndpointConnectionError

def safe_aws_call(fn, region):
    try:
        return fn()
    except (ClientError, EndpointConnectionError) as e:
        print(f"⚠️  Skipping region {region} → {type(e).__name__}: {getattr(e, 'response', {}).get('Error', {}).get('Code', str(e))}")
        return None

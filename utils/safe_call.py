from botocore.exceptions import ClientError, EndpointConnectionError

def safe_aws_call(fn, region):
    try:
        return fn()
    except (ClientError, EndpointConnectionError) as e:
        return None

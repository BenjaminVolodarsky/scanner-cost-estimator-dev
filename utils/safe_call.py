import botocore

def safe_aws_call(fn):
    try:
        return fn()
    except botocore.exceptions.ClientError:
        return None
    except Exception:
        return None

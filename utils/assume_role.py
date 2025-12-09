import boto3

def assume_role(account_id, role="UpwindEstimator"):
    sts = boto3.client("sts")

    try:
        creds = sts.assume_role(
            RoleArn=f"arn:aws:iam::{account_id}:role/{role}",
            RoleSessionName="UpwindCostScan"
        )["Credentials"]

        return boto3.Session(
            aws_access_key_id=creds["AccessKeyId"],
            aws_secret_access_key=creds["SecretAccessKey"],
            aws_session_token=creds["SessionToken"]
        )

    except Exception as e:
        return None

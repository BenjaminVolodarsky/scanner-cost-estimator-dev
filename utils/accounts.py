import boto3
import botocore

def list_org_accounts():
    try:
        client = boto3.client("organizations")
        accounts = []
        paginator = client.get_paginator("list_accounts")
        for page in paginator.paginate():
            accounts += [{"name": a["Name"], "account_id": a["Id"]} for a in page["Accounts"]]
        return accounts
    except Exception:
        print("⚠️ No Organizations access — scanning only this account.")
        sts = boto3.client("sts").get_caller_identity()
        return [{"name": "local", "account_id": sts["Account"]}]


def find_assumable_role(account_id):
    candidate_roles = [
        "OrganizationAccountAccessRole",
        f"AWSReservedSSO_Upwind*",   # auto-match SSO roles
        f"AWSReservedSSO_*",         # generic wildcard match
    ]

    sts = boto3.client("sts")

    # try common roles
    for role in candidate_roles:
        role_arn = f"arn:aws:iam::{account_id}:role/{role}"
        try:
            resp = sts.assume_role(
                RoleArn=role_arn,
                RoleSessionName="UpwindScanner"
            )
            creds = resp["Credentials"]
            return boto3.Session(
                aws_access_key_id=creds["AccessKeyId"],
                aws_secret_access_key=creds["SecretAccessKey"],
                aws_session_token=creds["SessionToken"]
            )
        except botocore.exceptions.ClientError:
            continue

    return None

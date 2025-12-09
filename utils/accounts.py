import boto3, botocore

def list_org_accounts():
    try:
        org = boto3.client("organizations")
        pages = org.get_paginator("list_accounts")
        accounts = []
        for p in pages.paginate():
            accounts += [{"account_id": a["Id"], "name": a["Name"]} for a in p["Accounts"]]
        return accounts
    except:
        # fallback single account mode
        acc = boto3.client("sts").get_caller_identity()["Account"]
        return [{"account_id": acc, "name": "Local"}]


def find_assumable_role(account_id):
    roles_to_try = [
        "OrganizationAccountAccessRole",      # default AWS org trust role
        "AWSReservedSSO_AdministratorAccess*", # SSO-based
        "AWSReservedSSO_*",
    ]

    sts = boto3.client("sts")
    for r in roles_to_try:
        role_arn = f"arn:aws:iam::{account_id}:role/{r}"
        try:
            resp = sts.assume_role(RoleArn=role_arn, RoleSessionName="UpwindScanner")
            return boto3.Session(
                aws_access_key_id=resp["Credentials"]["AccessKeyId"],
                aws_secret_access_key=resp["Credentials"]["SecretAccessKey"],
                aws_session_token=resp["Credentials"]["SessionToken"]
            )
        except botocore.exceptions.ClientError:
            continue

    return None

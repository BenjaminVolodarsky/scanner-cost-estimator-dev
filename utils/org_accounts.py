import boto3

def list_org_accounts():
    org = boto3.client("organizations")
    accounts = []

    paginator = org.get_paginator("list_accounts")
    for page in paginator.paginate():
        for acc in page["Accounts"]:
            if acc["Status"] == "ACTIVE":
                accounts.append({
                    "id": acc["Id"],
                    "name": acc["Name"]
                })

    return accounts

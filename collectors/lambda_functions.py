import boto3

def collect_lambda_functions(session, region, args=None):
    lambda_client = session.client("lambda", region_name=region)

    results = []

    try:
        paginator = lambda_client.get_paginator("list_functions")

        for page in paginator.paginate():
            for fn in page.get("Functions", []):
                results.append({
                    "resource": "lambda",
                    "region": region,
                    "memory_mb": fn.get("MemorySize"),
                    "code_size_mb": round(fn.get("CodeSize", 0) / 1024 / 1024, 3),
                })

    except Exception as e:
        return []

    return results

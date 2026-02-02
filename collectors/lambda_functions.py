def collect_lambda_functions(session, region, args=None, account_id="unknown"):
    lambda_client = session.client("lambda", region_name=region)
    results = []

    try:
        paginator = lambda_client.get_paginator("list_functions")
        for page in paginator.paginate():
            for fn in page.get("Functions", []):
                results.append({
                    "account_id": account_id,
                    "resource": "lambda",
                    "region": region,
                    "memory_mb": fn.get("MemorySize"),
                    "code_size_mb": round(fn.get("CodeSize", 0) / 1024 / 1024, 3),
                })
    except Exception as e:
        print(f"Access denied for Lambda in {account_id}")
        return []
    return results
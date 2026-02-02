def collect_lambda_functions(session, region, account_id):
    client = session.client("lambda", region_name=region)
    results = []
    error = None
    try:
        paginator = client.get_paginator('list_functions')
        for page in paginator.paginate():
            for func in page['Functions']:
                results.append({
                    "account_id": account_id,
                    "resource": "lambda",
                    "region": region,
                    "name": func.get('FunctionName'),
                    "memory_mb": func.get('MemorySize')
                })
    except Exception as e:
        if "AccessDenied" in str(e):
            error = "lambda:ListFunctions"
    return results, error

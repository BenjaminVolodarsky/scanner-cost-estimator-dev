import boto3

def collect_lambda_functions(session, region):
    lambda_client = session.client("lambda", region_name=region)

    results = []

    try:
        paginator = lambda_client.get_paginator("list_functions")

        for page in paginator.paginate():
            for fn in page.get("Functions", []):
                results.append({
                    "resource": "lambda",
                    "region": region,
                    "name": fn.get("FunctionName"),
                    "runtime": fn.get("Runtime"),
                    "handler": fn.get("Handler"),
                    "memory_mb": fn.get("MemorySize"),
                    "timeout_sec": fn.get("Timeout"),
                    "arch": fn.get("Architectures", []),
                    "last_modified": fn.get("LastModified"),
                    "code_size_mb": round(fn.get("CodeSize", 0) / 1024 / 1024, 3),
                    "env_vars": list(fn.get("Environment", {}).get("Variables", {}).keys()),
                    "vpc_enabled": "VpcConfig" in fn and fn["VpcConfig"].get("SubnetIds", []),
                    "tracing": fn.get("TracingConfig", {}).get("Mode"),
                    "tags": lambda_client.list_tags(
                        Resource=fn["FunctionArn"]
                    ).get("Tags", {})
                })

    except Exception as e:
        print(f"   ⚠️ Lambda scan failed in {region} → {e}")

    return results

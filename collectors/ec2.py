def collect_ec2_instances(session, region, args=None):
    ec2 = session.client("ec2", region_name=region)
    result = []
    skipped_asg = skipped_stopped = 0

    try:
        paginator = ec2.get_paginator("describe_instances")
        for page in paginator.paginate():
            for r in page.get("Reservations", []):
                for inst in r.get("Instances", []):
                    state = inst.get("State", {}).get("Name")
                    tags = {t["Key"]: t["Value"] for t in inst.get("Tags", [])}

                    if state == "stopped" and not args.include_stopped:
                        skipped_stopped += 1
                        continue

                    if "aws:autoscaling:groupName" in tags and not args.include_asg_instances:
                        skipped_asg += 1
                        continue

                    result.append({
                        "resource":"ec2",
                        "region":region,
                        "type":inst.get("InstanceType"),
                        "lifecycle":inst.get("InstanceLifecycle","on-demand")
                    })

    except: pass

    return result

def collect_ec2_instances(session, region, args=None):
    ec2 = session.client("ec2", region_name=region)
    result = []

    stopped_skipped = 0
    asg_members_skipped = 0

    try:
        paginator = ec2.get_paginator("describe_instances")
        for page in paginator.paginate():
            for reservation in page.get("Reservations", []):
                for inst in reservation.get("Instances", []):

                    state = inst.get("State", {}).get("Name")

                    if state == "stopped" and not args.include_stopped:
                        stopped_skipped += 1
                        continue

                    tags = {t["Key"]: t["Value"] for t in inst.get("Tags", [])}

                    if "aws:autoscaling:groupName" in tags and not args.include_asg_instances:
                        asg_members_skipped += 1
                        continue

                    result.append({
                        "resource": "ec2",
                        "region": region,
                        "type": inst.get("InstanceType"),
                        "lifecycle": inst.get("InstanceLifecycle", "on-demand")
                    })


    except Exception as e:
        print(f"⚠️ EC2 scan failed in {region} → {e}")

    print(f"   ✔ EC2 in {region}: {len(result)} collected "
          f"| 📴 skipped_stopped={stopped_skipped} | 🏷 skipped_asg_members={asg_members_skipped}")

    return result

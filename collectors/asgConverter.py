def collect_asg_as_ec2_equivalent(session, region, args=None):
    from collectors.asg import collect_auto_scaling_groups
    asgs = collect_auto_scaling_groups(session, region, args)

    virtual_ec2 = []

    for asg in asgs:
        virtual_ec2.append({
            "resource": "ec2",
            "region": region,
            "type": "asg",                             # <- requested format
            "asg_name": asg["name"],
            "counted_as": asg["counted_as"],           # 1 or instance count
            "kubernetes_detected": asg["kubernetes_detected"],
            "tags": asg["tags"]
        })

    return virtual_ec2

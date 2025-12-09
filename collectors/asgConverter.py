# collectors/asgConverter.py

from collectors.asg import collect_auto_scaling_groups

def collect_asg_as_ec2_equivalent(session, region, args=None):
    groups = collect_auto_scaling_groups(session, region, args)
    result = []

    for g in groups:
        count = g.get("desired", 1)

        # If include_asg_instances is OFF -> count ASG as 1 VM unit
        vm_count = count if args.include_asg_instances else 1

        for _ in range(vm_count):
            result.append({
                "resource": "ec2",
                "region": region,
                "type": "asg",
                "lifecycle": "unknown"
            })

    return result

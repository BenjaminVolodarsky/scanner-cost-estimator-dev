def generate_summary(results):
    summary = {
        "ec2": 0,
        "asg": 0,
        "ebs": 0,
        "ebs_total_gb": 0,
        "s3": 0,
        "s3_total_gb": 0,
        "lambda": 0,
    }

    for r in results:
        if r["resource"] == "ec2":
            if r.get("type") == "asg":
                summary["asg"] += 1
            else:
                summary["ec2"] += 1

        elif r["resource"] == "ebs":
            summary["ebs"] += 1
            summary["ebs_total_gb"] += r.get("size_gb", 0) or 0

        elif r["resource"] == "s3_bucket":
            summary["s3"] += 1
            summary["s3_total_gb"] += r.get("size_gb", 0) or 0

        elif r["resource"] == "lambda":
            summary["lambda"] += 1

    # Compute final scanning units (CloudScanner may treat ASG as 1 VM)
    summary["total_compute_units"] = summary["ec2"] + summary["asg"]

    return summary


def print_summary(summary):
    print("\n================ CloudScanner Estimated Scope ================")
    print(f"EC2 Instances:               {summary['ec2']}")
    print(f"AutoScaling Groups:          {summary['asg']} (counted as virtual EC2)")
    print(f"Compute Units Total:         {summary['total_compute_units']}")
    print("")
    print(f"S3 Buckets:                  {summary['s3']}  (total {round(summary['s3_total_gb'],2)} GB)")
    print(f"EBS Volumes:                 {summary['ebs']}  (total {round(summary['ebs_total_gb'],2)} GB)")
    print(f"Lambda Functions:            {summary['lambda']}")
    print("==============================================================\n")

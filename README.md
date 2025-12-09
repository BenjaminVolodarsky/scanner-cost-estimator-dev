# Upwind CloudScanner Cost Estimator

Lightweight read-only AWS footprint collector.  
Designed to estimate CloudScanner usage cost without deploying agents or running CloudFormation.

---

## What this tool collects

| Resource | Data collected |
|---|---|
| EC2 Instances | type + lifecycle (spot/on-demand), filtered by stopped/ASG rules |
| AutoScaling Groups | counted as 1 target by default or expanded via flag |
| EBS Volumes | type + size(GiB) |
| S3 Buckets | size estimate from CloudWatch metrics |
| Lambda Functions | memory + code size |

---

## Required IAM Permissions (Read-Only)

```json
{
  "Version": "2012-10-17",
  "Statement": [{
      "Effect": "Allow",
      "Action": [
        "ec2:DescribeInstances",
        "ec2:DescribeVolumes",
        "autoscaling:DescribeAutoScalingGroups",
        "s3:ListAllMyBuckets",
        "s3:GetBucketLocation",
        "cloudwatch:GetMetricStatistics",
        "lambda:ListFunctions",
        "lambda:ListTags"
      ],
      "Resource": "*"
  }]
}

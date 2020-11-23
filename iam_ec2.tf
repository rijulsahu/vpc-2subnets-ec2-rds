# iam role creation for EC2 with read and write access to both data and model S3 buckets
resource "aws_iam_role" "demo-ec2-iam-role" {
  name = "${var.project_prefix}-ec2-role-${var.env}"

  assume_role_policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": "sts:AssumeRole",
      "Principal": {
        "Service": "ec2.amazonaws.com"
      },
      "Effect": "Allow",
      "Sid": ""
    }
  ]
}
EOF

  tags = {
      tag-key = "${var.project_prefix}-ec2-role-${var.env}"
  }
}

# iam instance profile creation for ec2 access to S3 bucket
resource "aws_iam_instance_profile" "demo-ec2-iam-instance-profile" {
  name = "${var.project_prefix}-ec2-iam-instance-profile-${var.env}"
  role = "${aws_iam_role.demo-ec2-iam-role.name}"
}

# ec2 iam policy creation for read and write access to both data and model S3 buckets
resource "aws_iam_role_policy" "demo-ec2-iam-policy" {
  name = "${var.project_prefix}-ec2-iam-policy-${var.env}"
  role = "${aws_iam_role.demo-ec2-iam-role.id}"

policy = <<EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "ListObjectsInBucket",
            "Effect": "Allow",
            "Action": ["s3:ListBucket"],
            "Resource": ["arn:aws:s3:::${var.project_prefix}-data4-${var.env}"]
        },
        {
            "Sid": "AllObjectActions",
            "Effect": "Allow",
            "Action": [
              "s3:PutObject",
              "s3:GetObject",
              "s3:DeleteObject"
            ],
            "Resource": ["arn:aws:s3:::${var.project_prefix}-data4-${var.env}/*"]
        }
    ]
}
EOF
}

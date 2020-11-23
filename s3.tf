# Data bucket creation for demo
resource "aws_s3_bucket" "demo-data" {
  bucket = "${var.project_prefix}-data4-${var.env}"

  acl           = "private"
  force_destroy = true

  tags = {
    Name = "Data bucket for demo"
  }
}

# Block public access to Data bucket
resource "aws_s3_bucket_public_access_block" "demo-data-block" {
  bucket = aws_s3_bucket.demo-data.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

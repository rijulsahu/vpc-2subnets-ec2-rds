# Create elastic ip for Web application server
resource "aws_eip" "demo-web-ip" {
    vpc      = true
    instance = aws_instance.demo-ec2.id
    tags = {
    Name = "${var.project_prefix}-elastic-ip-${var.env}"
  }
}

output "demo_PublicIP" {
    value = aws_eip.demo-web-ip.public_ip
}

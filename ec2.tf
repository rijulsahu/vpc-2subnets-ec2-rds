# Create ec2 instance in public subnet
resource "aws_instance" "demo-ec2" {
  ami           = "ami-0e9182bc6494264a4"
  instance_type = "t2.medium"
  iam_instance_profile = "${aws_iam_instance_profile.demo-ec2-iam-instance-profile.name}"
  availability_zone = "ap-south-1a"
  subnet_id     = aws_subnet.demo-public-subnet.id
  #key_name      = "${var.project_prefix}-ec2-key-${var.env}"
  key_name      = "MyEC2Key"
  vpc_security_group_ids = [ aws_security_group.demo-web-sg.id ]
  user_data = file("server-script.sh")

  tags = {
    Name = "${var.project_prefix}-ec2-${var.env}"
  }
  depends_on = [ aws_subnet.demo-public-subnet]
}

# Create ebs volume
resource "aws_ebs_volume" "demo-ebs" {
    availability_zone = "ap-south-1a"
    size = var.ebs_storage
    type = "gp2"
    tags =  {
        Name = "${var.project_prefix}-webserver-storage-${var.env}"
    }
}

# Attach ebs to instance
resource "aws_volume_attachment" "ebs-volume-1-attachment" {
  device_name = "/dev/sdh"
  volume_id = aws_ebs_volume.demo-ebs.id
  instance_id = aws_instance.demo-ec2.id
}

# Instance ID
output "instance_id" {
  description = "ID of the EC2 instance"
  value       = aws_instance.main.id
}

# Public IP Address
output "public_ip" {
  description = "Public IP address of the EC2 instance"
  value       = aws_instance.main.public_ip
}

# Key Pair Name
output "key_pair_name" {
  description = "Name of the key pair used for SSH access"
  value       = var.create_key_pair ? aws_key_pair.main[0].key_name : data.aws_key_pair.existing[0].key_name
}

# Security Group ID
output "security_group_id" {
  description = "ID of the security group"
  value       = aws_security_group.main.id
}

# AMI ID
output "ami_id" {
  description = "ID of the AMI used for the instance"
  value       = data.aws_ami.amazon_linux.id
}

# Instance State
output "instance_state" {
  description = "State of the EC2 instance"
  value       = aws_instance.main.instance_state
}

# SSH Connection Command
output "ssh_connection" {
  description = "SSH connection command"
  value       = "ssh -i ~/.ssh/id_rsa ec2-user@${aws_instance.main.public_ip}"
}
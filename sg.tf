#Security group for public facing webserver
resource "aws_security_group" "demo-web-sg" {
  name = "${var.project_prefix}-web-sg-${var.env}"
  description = "Allow HTTP/HTTPS/SSH/PING"
  ingress {
    from_port = 80
    to_port = 80
    protocol = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  ingress {
    description = "HTTPS"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = [ "0.0.0.0/0" ]
  }
  ingress {
    from_port = -1
    to_port = -1
    protocol = "icmp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  ingress {
    from_port = 22
    to_port = 22
    protocol = "tcp"
    cidr_blocks =  ["0.0.0.0/0"]
  }
  egress {
    from_port       = 0
    to_port         = 0
    protocol        = "-1"
    cidr_blocks     = ["0.0.0.0/0"]
  }
  vpc_id            = aws_vpc.demo-vpc.id
  tags              = {
    Name = "${var.project_prefix}-web-sg-${var.env}"
  }
}

#Security group for private database server
resource "aws_security_group" "demo-database-sg" {
  name = "${var.project_prefix}-database-sg-${var.env}"
  description = "Allow connection from Web server SG"
  ingress {
    from_port = 5432
    to_port = 5432
    protocol = "tcp"
    cidr_blocks = ["10.0.1.0/24"]
  }

  egress {
    from_port       = 0
    to_port         = 0
    protocol        = "-1"
    cidr_blocks     = ["0.0.0.0/0"]
  }
  vpc_id            = "${aws_vpc.demo-vpc.id}"
  tags              = {
    Name = "${var.project_prefix}-database-sg-${var.env}"
  }
}

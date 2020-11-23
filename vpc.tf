#VPC
resource "aws_vpc" "demo-vpc" {
    cidr_block = "10.0.0.0/16"
    enable_dns_hostnames = true
    tags = {
    Name = "${var.project_prefix}-vpc-${var.env}"
  }
}

#Public Subnet
resource "aws_subnet" "demo-public-subnet" {
  vpc_id     = aws_vpc.demo-vpc.id
  cidr_block = "10.0.1.0/24"
  availability_zone = "ap-south-1a"
  map_public_ip_on_launch = "true"
  tags = {
    Name = "${var.project_prefix}-public-subnet-${var.env}"
  }
}

#Private Subnet 1
resource "aws_subnet" "demo-private-subnet1" {
  vpc_id     = aws_vpc.demo-vpc.id
  cidr_block = "10.0.2.0/24"
  availability_zone = "ap-south-1a"
  tags = {
    Name = "${var.project_prefix}-private-subnet1-${var.env}"
  }
}

#Private Subnet 2
resource "aws_subnet" "demo-private-subnet2" {
  vpc_id     = aws_vpc.demo-vpc.id
  cidr_block = "10.0.3.0/24"
  availability_zone = "ap-south-1b"
  tags = {
    Name = "${var.project_prefix}-private-subnet2-${var.env}"
  }
}

#internet Gateway for public subnet
resource "aws_internet_gateway" "demo-ig" {
  vpc_id = aws_vpc.demo-vpc.id
  tags = {
    Name = "${var.project_prefix}-ig-${var.env}"
  }
  depends_on = [ aws_vpc.demo-vpc]
}

#DB Subnet group for posgresql
resource "aws_db_subnet_group" "demo-db-subnet-group" {
  name       = "${var.project_prefix}-db-subnet-group-${var.env}"
  subnet_ids = [aws_subnet.demo-private-subnet1.id, aws_subnet.demo-private-subnet2.id]
  #subnet_ids = [aws_subnet.mktmsosprivatesubnet.id]
  tags = {
    Name = "${var.project_prefix}-db-subnet-group-${var.env}"
  }
}

#Route table for public subnet
resource "aws_route_table" "demo-public-rtb" {
  vpc_id = aws_vpc.demo-vpc.id
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.demo-ig.id
  }
  tags = {
    Name = "${var.project_prefix}-public-rtb-${var.env}"
  }
  depends_on = [ aws_internet_gateway.demo-ig]
}

#Route table for association to public subnet
resource "aws_route_table_association" "association-public-routing-table" {
  subnet_id      = aws_subnet.demo-public-subnet.id
  route_table_id = aws_route_table.demo-public-rtb.id
  depends_on = [aws_route_table.demo-public-rtb]
  }

#Route table for private subnet
resource "aws_route_table" "demo-private-rtb" {
  vpc_id = aws_vpc.demo-vpc.id
  tags = {
    Name = "${var.project_prefix}-private-rtb-${var.env}"
  }
  #depends_on = [ aws_internet_gateway.mktmsosstageig]
}

#Route table for association to private subnet1
resource "aws_route_table_association" "association1-private-routing-table" {
  subnet_id      = aws_subnet.demo-private-subnet1.id
  route_table_id = aws_route_table.demo-private-rtb.id
  depends_on = [aws_route_table.demo-private-rtb]
  }

#Route table for association to private subnet2
resource "aws_route_table_association" "association2-private-routing-table" {
  subnet_id      = aws_subnet.demo-private-subnet2.id
  route_table_id = aws_route_table.demo-private-rtb.id
  depends_on = [aws_route_table.demo-private-rtb]
  }

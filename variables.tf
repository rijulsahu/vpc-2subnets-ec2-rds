variable "env" {
  type    = string
  default = "prod"
}

variable "project_prefix" {
  type    = string
  default = "demo"
}

# DB Variables
variable "db_admin_user" {
  type    = string
  default = "demo_db_admin_prod"
}

variable "rds_password" {
  type    = string
  description= "Enter the password for rds db"
}

variable "db_storage" {
  type    = number
  default = 20
}

# EC2 variables
variable "ebs_storage" {
  type    = number
  default = 100
}

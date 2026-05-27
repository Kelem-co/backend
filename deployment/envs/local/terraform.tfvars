region      = "us-east-1"
environment = "local"
namespace   = "kelem"

tags = {
  owner      = "platform"
  managed-by = "terraform"
}

vpc_cidr_block     = "10.42.0.0/16"
availability_zones = ["us-east-1a"]
ssh_cidr_blocks    = ["0.0.0.0/0"]

security_group_rules = [
  {
    type        = "ingress"
    from_port   = 8000
    to_port     = 8000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  },
  {
    type        = "ingress"
    from_port   = 9025
    to_port     = 9025
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  },
]

user_data_template_vars = {
  INSTANCE_NAME      = "kelem-dev-instance"
  DEFAULT_LOGIN_USER = "ubuntu"
}

instance_type = "t3.small"
ami_names     = ["ubuntu-22.04-jammy-jellyfish"]
ami_owners    = ["000000000000"] # LocalStack
volume_size   = 30

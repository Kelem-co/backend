region      = "us-east-1"
environment = "dev"
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
ami_names     = ["ubuntu/images/hvm-ssd-gp3/ubuntu-noble-24.04-amd64-server-*"]
ami_owners    = ["099720109477"]
volume_size   = 30

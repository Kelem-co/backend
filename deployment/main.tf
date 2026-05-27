data "aws_ami" "this" {
  most_recent = true

  filter {
    name   = "name"
    values = var.ami_names
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }

  owners = var.ami_owners
}

resource "tls_private_key" "this" {
  algorithm = "RSA"
  rsa_bits  = 4096
}

resource "aws_key_pair" "this" {
  key_name   = "${local.namespace}-key-pair"
  public_key = tls_private_key.this.public_key_openssh

  tags = merge(
    var.tags,
    {
      Name = "${local.namespace}-key-pair"
    }
  )
}

resource "aws_instance" "this" {
  #checkov:skip=CKV2_AWS_41
  count = length(var.availability_zones)

  availability_zone = element(var.availability_zones, count.index)
  ami               = data.aws_ami.this.id
  instance_type     = var.instance_type

  subnet_id              = aws_subnet.public_subnet[count.index].id
  vpc_security_group_ids = [aws_security_group.this.id]

  associate_public_ip_address = true

  key_name  = aws_key_pair.this.key_name
  user_data = local.user_data

  metadata_options {
    http_endpoint               = "enabled"
    http_tokens                 = "required"
    http_put_response_hop_limit = 1
  }

  root_block_device {
    volume_type           = "gp3"
    volume_size           = var.volume_size
    delete_on_termination = true
  }

  lifecycle {
    ignore_changes = [
      ami,
      user_data,
    ]
  }

  tags = merge(
    local.common_tags,
    {
      Name = "${local.namespace}-instance"
    }
  )

}

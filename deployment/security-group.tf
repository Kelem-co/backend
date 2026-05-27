resource "aws_security_group" "this" {
  name_prefix = "${local.namespace}-sg-"
  vpc_id      = aws_vpc.vpc.id
  description = "Security group for ${local.namespace}"

  tags = merge(
    local.common_tags,
    {
      Name = "${local.namespace}-sg"
    }
  )
}

resource "aws_vpc_security_group_ingress_rule" "ssh" {
  for_each = toset(var.ssh_cidr_blocks)

  security_group_id = aws_security_group.this.id
  description       = "Allow SSH access"
  from_port         = 22
  to_port           = 22
  ip_protocol       = "tcp"
  cidr_ipv4         = each.key
}

resource "aws_vpc_security_group_egress_rule" "all" {
  security_group_id = aws_security_group.this.id
  description       = "Allow outbound internet access"
  from_port         = 0
  to_port           = 0
  ip_protocol       = "-1"
  cidr_ipv4         = "0.0.0.0/0"
}

resource "aws_security_group_rule" "additional" {
  for_each = {
    for idx, rule in var.security_group_rules : idx => rule
  }

  security_group_id        = aws_security_group.this.id
  type                     = each.value.type
  from_port                = each.value.from_port
  to_port                  = each.value.to_port
  protocol                 = each.value.protocol
  cidr_blocks              = lookup(each.value, "cidr_blocks", null)
  source_security_group_id = lookup(each.value, "source_security_group_id", null)
  description              = lookup(each.value, "description", null)
}

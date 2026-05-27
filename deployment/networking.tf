resource "aws_vpc" "vpc" {
  #checkov:skip=CKV2_AWS_11
  cidr_block = var.vpc_cidr_block

  tags = merge(
    local.common_tags,
    {
      Name = "${local.namespace}-vpc"
    }
  )
}

resource "aws_default_security_group" "default" {
  vpc_id = aws_vpc.vpc.id

  tags = merge(
    local.common_tags,
    {
      Name = "${local.namespace}-default-sg"
    }
  )
}


resource "aws_internet_gateway" "default" {
  vpc_id = aws_vpc.vpc.id

  tags = merge(
    local.common_tags,
    {
      Name = "${local.namespace}-igw"
    }
  )
}

resource "aws_subnet" "public_subnet" {
  vpc_id = aws_vpc.vpc.id
  count  = length(var.availability_zones)

  cidr_block        = cidrsubnet(var.vpc_cidr_block, 8, count.index + length(var.availability_zones) + 1)
  availability_zone = element(var.availability_zones, count.index)

  tags = merge(
    local.common_tags,
    {
      Name = "${local.namespace}-public-subnet-${count.index + 1}"
    }
  )
}

resource "aws_route_table" "public_route_table" {
  vpc_id = aws_vpc.vpc.id

  route {
    cidr_block = var.destination_cidr_block
    gateway_id = aws_internet_gateway.default.id
  }

  tags = merge(
    local.common_tags,
    {
      Name = "${local.namespace}-public-rt"
    }
  )
}

resource "aws_route_table_association" "public_subnet_association" {
  subnet_id      = aws_subnet.public_subnet[count.index].id
  route_table_id = aws_route_table.public_route_table.id
  count          = length(var.availability_zones)
}

resource "aws_main_route_table_association" "main_route_table_association" {
  vpc_id         = aws_vpc.vpc.id
  route_table_id = aws_route_table.public_route_table.id
}

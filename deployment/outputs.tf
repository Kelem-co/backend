output "vpc_id" {
  description = "ID of the VPC where the cluster is deployed"
  value       = aws_vpc.vpc.id
}

output "subnet_id" {
  value       = aws_subnet.public_subnet[0].id
  description = "ID of the public subnet where the instance is deployed"
}

output "subnet_cidr_block" {
  value       = aws_subnet.public_subnet[0].cidr_block
  description = "CIDR block of the public subnet where the instance is deployed"
}

output "key_pair" {
  value       = tls_private_key.this.private_key_pem
  description = "Private key for the EC2 instance. Keep this secret!"
  sensitive   = true
}

output "instance_arn" {
  value       = aws_instance.this[0].arn
  description = "ARN of the ClickHouse EC2 instance"
}

output "template_render" {
  value       = local.user_data
  description = "Rendered user data template"
}

output "instance_public_ip" {
  value       = aws_instance.this[0].public_ip
  description = "Public IPv4 address assigned to the ClickHouse instance"
}

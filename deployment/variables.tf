variable "region" {
  description = "Region where to deploy the resources"
  type        = string
}

variable "environment" {
  type        = string
  description = "The environment where to deploy the solution"

  validation {
    condition     = contains(["dev", "test", "prod", "local"], var.environment)
    error_message = "environment must be one of: dev, test, prod, local."
  }
}

variable "namespace" {
  type        = string
  description = "Namespace for resource names"
}

variable "tags" {
  type        = map(string)
  description = "Additional tags to apply to resources"
  default     = {}
}

variable "vpc_cidr_block" {
  type        = string
  description = "CIDR block for the VPC"
}

variable "availability_zones" {
  type        = list(string)
  description = "List of availability zones. Example: eu-west-1a and eu-west-1b"
}

variable "destination_cidr_block" {
  type        = string
  description = "CIDR block for the default route (e.g., 0.0.0.0/0)"
  default     = "0.0.0.0/0"
}

variable "ssh_cidr_blocks" {
  description = "CIDR blocks allowed to reach SSH on the cluster instances."
  type        = list(string)
  default     = []
}

variable "security_group_rules" {
  description = "Additional security group rules for the cluster instances."
  type = list(object({
    type                     = string
    from_port                = number
    to_port                  = number
    protocol                 = string
    cidr_blocks              = optional(list(string))
    source_security_group_id = optional(string)
    description              = optional(string)
  }))
  default = []
}

variable "instance_type" {
  description = "EC2 instance type for the cluster nodes."
  type        = string
}

variable "user_data_template_vars" {
  description = "Variables to render the user data template with."
  type        = map(string)
  default     = {}
}

variable "volume_size" {
  type        = number
  description = "Size in GiB for the root EBS volume attached to instances"
}

variable "ami_names" {
  type        = list(string)
  description = "Ordered list of AMI name patterns to search for (fallback order)"
}

variable "ami_owners" {
  type        = list(string)
  description = "List of AWS account IDs (or 'self') that own acceptable AMIs"
}

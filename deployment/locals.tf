locals {
  namespace = lower(var.namespace)

  common_tags = merge(
    var.tags,
    {
      namespace   = local.namespace
      environment = var.environment
    }
  )

  user_data = templatefile("${path.module}/${var.user_data_template_file}", var.user_data_template_vars)
}

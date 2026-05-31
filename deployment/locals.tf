locals {
  namespace = lower(var.namespace)

  common_tags = merge(
    var.tags,
    {
      namespace   = local.namespace
      environment = var.environment
    }
  )

  user_data = templatefile(
    "${path.module}/${var.user_data_template_file}",
    merge(
      var.user_data_template_vars,
      {
        SWAP_SIZE_MIB = tostring(var.swap_size_mib)
      }
    )
  )
}

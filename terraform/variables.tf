variable "app_name" {
  default = "hydrocron"
}
variable "stage" {
  type = string
}

variable "default_tags" {
  type    = map(string)
  default = {}
}

variable "app_version" {
  type = string
}

variable "lambda_container_image_uri" {
  type = string
}

variable "cross_account_ids" {
  type        = list(string)
  description = "Cross account identifiers for Cumulus Topic publication"

  validation {
    condition     = length(var.cross_account_ids) > 0 && alltrue([for account_id in var.cross_account_ids : length(regexall("^\\d{12}$", account_id)) > 0])
    error_message = "cross_account_ids must contain one or more 12-digit AWS account IDs."
  }
}

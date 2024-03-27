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

variable "cross_account_id" {
  type        = string
  description = "Cross account identifier for Cumulus Topic publication"
}
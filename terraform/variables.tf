variable "app_name" {default = "hydrocron-api"}
variable "db_app_name" {default = "hydrocron-db"}
variable "stage" {}
variable "vpc_id" {}
variable "private_subnets" {}
variable "default_vpc_sg" {}
variable "image" {default = ""}

variable "default_tags" {
  type = map(string)
  default = {}
}

variable "app_version" {
  default = ""
}

variable "credentials" {
  default = "~/.aws/credentials"
}

variable "profile" {
  default = "ngap-service-sit"
}

variable "docker_tag" {
  default = "ghcr.io/podaac/hydrocron:sit"
}

variable "service_name" {
    default = "hydrocron-api"
    type = string
}

variable "lambda_container_image_uri" {
  type = string
  default = "hydrocron-container-image"
}
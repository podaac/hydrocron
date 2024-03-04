terraform {

  backend "s3" {
    # This must be updated for each unique deployment/stage!
    # should  be of the form services/APP_NAME/STAGE/terraform.tfstate
    # We can't use variables in the key name here, so we need to be extra
    # careful with this!
    key = "services/hydrocron/terraform.tfstate"
    region = "us-west-2"
  }

  required_providers {
    aws      = ">= 3.50.0"
    template = ">= 2.2.0"
  }
  required_version = ">= 1.3.7"
}

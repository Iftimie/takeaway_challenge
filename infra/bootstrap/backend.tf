# Activate as backend.tf only after the first local-state apply succeeds.
terraform {
  backend "s3" {
    bucket              = "takeaway-tfstate-455958489157-eu-north-1"
    key                 = "bootstrap/terraform.tfstate"
    region              = "eu-north-1"
    allowed_account_ids = ["455958489157"]
    encrypt             = true
    use_lockfile        = true
  }
}

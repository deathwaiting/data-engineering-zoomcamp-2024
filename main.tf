terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "5.6.0"
    }
  }
}

provider "google" {
  project     = var.project
  region      = var.region
}


resource "google_storage_bucket" "demo-bucket" {
  name          = "${var.gcs_bucket_name}"
  location      = var.location
  force_destroy = true


  lifecycle_rule {
    condition {
      age = 1
    }
    action {
      type = "AbortIncompleteMultipartUpload"
    }
  }
}



resource "google_bigquery_dataset" "demo-dataset" {
  dataset_id = "${var.bq_dataset_name}"
  location   = var.location
}


# resource "google_project_service" "enable_dataproc_google_apis" {
#   project = var.project
#   service = "dataproc.googleapis.com"
#   disable_dependent_services = true
# }
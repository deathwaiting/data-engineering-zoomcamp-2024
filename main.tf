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

###############################################################
## configure dataproc according to this blog
## https://medium.com/google-cloud/deploying-google-cloud-dataproc-with-terraform-what-why-and-how-74e26366d092
###############################################################

## Start with creating storage bucket, service account and assigning them the appropriate roles.

resource "google_service_account" "dataproc-svc" {
  project      = var.project
  account_id   = "dataproc-svc"
  display_name = "Service Account - dataproc"
}

resource "google_project_iam_member" "svc-access" {
  project = var.project
  role    = "roles/dataproc.worker"
  member  = "serviceAccount:${google_service_account.dataproc-svc.email}"
}

resource "google_storage_bucket" "dataproc-bucket" {
  project                     = var.project
  name                        = "${var.prefix}-dataproc-config"
  uniform_bucket_level_access = true
  location                    = var.region
}

resource "google_storage_bucket_iam_member" "dataproc-member" {
  bucket = google_storage_bucket.dataproc-bucket.name
  role   = "roles/storage.admin"
  member = "serviceAccount:${google_service_account.dataproc-svc.email}"
}




resource "google_project_service" "enable_dataproc_google_apis" {
  project = var.project
  service = "dataproc.googleapis.com"
  disable_dependent_services = true
}


resource "google_dataproc_cluster" "mycluster" {
  name                          = "${var.prefix}-dataproc"
  region                        = var.region
  depends_on = [ google_project_service.enable_dataproc_google_apis ]

  cluster_config {
    staging_bucket = google_storage_bucket.dataproc-bucket.name

    #The flag to enable http access to specific ports on the cluster from external sources (aka Component Gateway). Defaults to false.
    #This should create the cluster with jupyter included
    endpoint_config {
      enable_http_port_access = true
    }

    #We are creating a single node cluster, so, no need for workers for now
    master_config {
      num_instances = 1
      machine_type  = var.dataproc_master_machine_type
      disk_config {
        boot_disk_type    = "pd-standard"
        boot_disk_size_gb = var.dataproc_master_bootdisk
      }
    }

    # worker_config {
    #   num_instances = var.dataproc_workers_count
    #   machine_type  = var.dataproc_worker_machine_type
    #   disk_config {
    #     boot_disk_type    = "pd-standard"
    #     boot_disk_size_gb = var.dataproc_worker_bootdisk
    #     num_local_ssds    = var.worker_local_ssd
    #   }
    # }

    # preemptible_worker_config {
    #   num_instances = var.preemptible_worker
    # }

    software_config {
      image_version = "2.0.66-debian10"
      optional_components = ["JUPYTER"]
      override_properties = {
        # create a single node cluster to reduce costs
        "dataproc:dataproc.allow.zero.workers" = true
        # "dataproc:dataproc.jupyter.listen.all.interfaces" = true
        "dataproc:dataproc.jupyter.notebook.gcs.dir" = google_storage_bucket.dataproc-bucket.name
      }
    }

    gce_cluster_config {
      zone = "${var.region}-b"
      service_account        = google_service_account.dataproc-svc.email
      service_account_scopes = ["cloud-platform"]
    }
  }
}
terraform {
  required_version = ">= 1.5"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# ─── Service Account ──────────────────────────────────────────────────────────

resource "google_service_account" "backend" {
  account_id   = "incident-copilot-backend"
  display_name = "Incident Copilot Backend SA"
}

# ─── IAM ──────────────────────────────────────────────────────────────────────

resource "google_project_iam_member" "bq_data_viewer" {
  project = var.project_id
  role    = "roles/bigquery.dataViewer"
  member  = "serviceAccount:${google_service_account.backend.email}"
}

resource "google_project_iam_member" "bq_job_user" {
  project = var.project_id
  role    = "roles/bigquery.jobUser"
  member  = "serviceAccount:${google_service_account.backend.email}"
}

resource "google_project_iam_member" "secret_accessor" {
  project = var.project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${google_service_account.backend.email}"
}

# ─── Secrets ──────────────────────────────────────────────────────────────────

resource "google_secret_manager_secret" "openai_api_key" {
  secret_id = "openai-api-key"
  replication {
    auto {}
  }
}

resource "google_secret_manager_secret" "pinecone_api_key" {
  secret_id = "pinecone-api-key"
  replication {
    auto {}
  }
}

# ─── BigQuery ─────────────────────────────────────────────────────────────────

resource "google_bigquery_dataset" "main" {
  dataset_id                  = var.bigquery_dataset
  location                    = "US"
  description                 = "Incident Copilot — service logs, metrics, and trace data"
  delete_contents_on_destroy  = false
}

resource "google_bigquery_table" "service_logs" {
  dataset_id = google_bigquery_dataset.main.dataset_id
  table_id   = "service_logs"
  deletion_protection = false

  time_partitioning {
    type  = "DAY"
    field = "timestamp"
  }

  schema = jsonencode([
    { name = "timestamp",    type = "TIMESTAMP", mode = "REQUIRED" },
    { name = "service_name", type = "STRING",    mode = "REQUIRED" },
    { name = "severity",     type = "STRING",    mode = "REQUIRED" },
    { name = "message",      type = "STRING",    mode = "REQUIRED" },
    { name = "trace_id",     type = "STRING",    mode = "NULLABLE" },
  ])
}

resource "google_bigquery_table" "service_metrics" {
  dataset_id = google_bigquery_dataset.main.dataset_id
  table_id   = "service_metrics"
  deletion_protection = false

  time_partitioning {
    type  = "DAY"
    field = "timestamp"
  }

  schema = jsonencode([
    { name = "timestamp",    type = "TIMESTAMP", mode = "REQUIRED" },
    { name = "service_name", type = "STRING",    mode = "REQUIRED" },
    { name = "metric_name",  type = "STRING",    mode = "REQUIRED" },
    { name = "value",        type = "FLOAT64",   mode = "REQUIRED" },
  ])
}

resource "google_bigquery_table" "trace_log" {
  dataset_id = google_bigquery_dataset.main.dataset_id
  table_id   = "trace_log"
  deletion_protection = false

  time_partitioning {
    type  = "DAY"
    field = "timestamp"
  }

  schema = jsonencode([
    { name = "trace_id",    type = "STRING",    mode = "REQUIRED" },
    { name = "timestamp",   type = "TIMESTAMP", mode = "REQUIRED" },
    { name = "endpoint",    type = "STRING",    mode = "NULLABLE" },
    { name = "method",      type = "STRING",    mode = "NULLABLE" },
    { name = "client_host", type = "STRING",    mode = "NULLABLE" },
  ])
}

# ─── VPC Connector ────────────────────────────────────────────────────────────

resource "google_vpc_access_connector" "main" {
  name          = "incident-copilot-connector"
  region        = var.region
  network       = "default"
  ip_cidr_range = "10.8.0.0/28"
  min_throughput = 200
  max_throughput = 1000
}

# ─── Cloud Run ────────────────────────────────────────────────────────────────

resource "google_cloud_run_v2_service" "backend" {
  name     = "incident-copilot-backend"
  location = var.region

  template {
    service_account = google_service_account.backend.email

    vpc_access {
      connector = google_vpc_access_connector.main.id
      egress    = "PRIVATE_RANGES_ONLY"
    }

    containers {
      image = var.backend_image

      resources {
        limits = {
          cpu    = "2"
          memory = "2Gi"
        }
      }

      env {
        name = "OPENAI_API_KEY"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.openai_api_key.secret_id
            version = "latest"
          }
        }
      }

      env {
        name = "PINECONE_API_KEY"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.pinecone_api_key.secret_id
            version = "latest"
          }
        }
      }

      env {
        name  = "GCP_PROJECT_ID"
        value = var.project_id
      }

      env {
        name  = "BIGQUERY_DATASET"
        value = var.bigquery_dataset
      }

      env {
        name  = "PINECONE_ENVIRONMENT"
        value = var.pinecone_env
      }

      env {
        name  = "LOG_LEVEL"
        value = "INFO"
      }

      startup_probe {
        http_get {
          path = "/health"
          port = 8000
        }
        initial_delay_seconds = 10
        period_seconds        = 5
        failure_threshold     = 10
      }

      liveness_probe {
        http_get {
          path = "/health"
          port = 8000
        }
        period_seconds    = 30
        failure_threshold = 3
      }
    }

    scaling {
      min_instance_count = 1
      max_instance_count = 20
    }
  }

  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }

  depends_on = [
    google_project_iam_member.bq_data_viewer,
    google_project_iam_member.bq_job_user,
    google_project_iam_member.secret_accessor,
  ]
}

# Allow unauthenticated invocations from frontend
resource "google_cloud_run_v2_service_iam_member" "public" {
  location = google_cloud_run_v2_service.backend.location
  name     = google_cloud_run_v2_service.backend.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

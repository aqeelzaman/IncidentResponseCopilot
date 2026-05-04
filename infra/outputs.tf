output "cloud_run_url" {
  description = "URL of the deployed Cloud Run backend service"
  value       = google_cloud_run_v2_service.backend.uri
}

output "bigquery_dataset_id" {
  description = "Full BigQuery dataset ID"
  value       = google_bigquery_dataset.main.dataset_id
}

output "backend_service_account_email" {
  description = "Service account email used by Cloud Run"
  value       = google_service_account.backend.email
}

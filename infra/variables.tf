variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "region" {
  description = "GCP region for Cloud Run and BigQuery"
  type        = string
  default     = "us-central1"
}

variable "pinecone_env" {
  description = "Pinecone environment (e.g. us-east-1)"
  type        = string
  default     = "us-east-1"
}

variable "backend_image" {
  description = "Container image for the FastAPI backend (e.g. gcr.io/project/incident-copilot:latest)"
  type        = string
}

variable "bigquery_dataset" {
  description = "BigQuery dataset name"
  type        = string
  default     = "incident_copilot"
}

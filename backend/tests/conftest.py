import os

import pytest

# Provide dummy env vars so imports don't fail
os.environ.setdefault("GROQ_API_KEY", "gsk-test-dummy")
os.environ.setdefault("PINECONE_API_KEY", "test-dummy")
os.environ.setdefault("GCP_PROJECT_ID", "test-project")
os.environ.setdefault("BIGQUERY_DATASET", "incident_copilot")


@pytest.fixture
def sample_incident() -> str:
    return (
        "checkout-service is returning 503s, orders are failing, "
        "started about 90 minutes ago"
    )


@pytest.fixture
def sample_trace_id() -> str:
    return "test-trace-12345"

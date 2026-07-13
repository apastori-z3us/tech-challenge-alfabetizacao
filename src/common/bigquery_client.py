from __future__ import annotations

from google.cloud import bigquery

from src.common.settings import Settings


def create_bigquery_client(settings: Settings) -> bigquery.Client:
    """Cria um cliente autenticado do BigQuery."""
    return bigquery.Client(
        project=settings.google_cloud_project,
        location=settings.bigquery_location,
    )
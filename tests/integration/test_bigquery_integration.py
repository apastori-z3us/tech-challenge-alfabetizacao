"""Testes de integração com BigQuery.

Marcados como `integration` e **pulados** quando as credenciais não estão
presentes (nunca rodam automaticamente no CI sem segredo). Habilite com:
    RUN_BQ_INTEGRATION=1 python -m pytest -m integration
"""

from __future__ import annotations

import os

import pytest

pytestmark = pytest.mark.integration

_ENABLED = os.getenv("RUN_BQ_INTEGRATION") == "1"


@pytest.mark.skipif(not _ENABLED, reason="Credenciais BigQuery ausentes.")
def test_bigquery_connectivity():
    from src.common.bigquery_client import create_bigquery_client
    from src.common.settings import load_settings

    settings = load_settings()
    client = create_bigquery_client(settings)
    rows = list(client.query("SELECT 1 AS ok").result())
    assert rows[0]["ok"] == 1


@pytest.mark.skipif(not _ENABLED, reason="Credenciais BigQuery ausentes.")
def test_municipio_source_exists():
    from src.batch.extractor import BigQueryReader, extract_to_bronze
    from src.batch.registry import get_source
    from src.common.bigquery_client import create_bigquery_client
    from src.common.settings import load_settings

    settings = load_settings()
    client = create_bigquery_client(settings)
    source = get_source(settings, "municipio")
    result = extract_to_bronze(settings, source, BigQueryReader(client))
    assert result.records_read > 0

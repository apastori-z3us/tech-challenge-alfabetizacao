"""Fixtures compartilhadas dos testes.

Define variáveis de ambiente padrão (para rodar sem `.env`), um `Settings`
apontando para um diretório temporário e amostras pequenas por entidade.
Nenhum teste unitário depende de BigQuery ou Docker.
"""

from __future__ import annotations

import os

# Variáveis mínimas para permitir load_settings() sem um .env real (ex.: CI).
os.environ.setdefault("GOOGLE_CLOUD_PROJECT", "rising-reserve-352718")
os.environ.setdefault("BQ_LOCATION", "US")
os.environ.setdefault("BQ_DATASET_BRONZE", "tc_alfabetizacao_bronze")
os.environ.setdefault("BQ_DATASET_SILVER", "tc_alfabetizacao_silver")
os.environ.setdefault("BQ_DATASET_GOLD", "tc_alfabetizacao_gold")
os.environ.setdefault("BQ_DATASET_AUDIT", "tc_alfabetizacao_audit")

import dataclasses  # noqa: E402

import pandas as pd  # noqa: E402
import pytest  # noqa: E402

from src.common.settings import Settings, load_settings  # noqa: E402


@pytest.fixture
def settings(tmp_path) -> Settings:
    """Settings com todos os caminhos redirecionados para um tmp isolado."""
    base = load_settings()
    data_root = tmp_path / "data"
    return dataclasses.replace(
        base,
        data_root=data_root,
        bronze_path=data_root / "bronze",
        silver_path=data_root / "silver",
        gold_path=data_root / "gold",
        audit_path=data_root / "audit",
        quarantine_path=data_root / "quarantine",
    )


@pytest.fixture
def municipio_bronze() -> pd.DataFrame:
    """Amostra Bronze de municípios com metadados de ingestão."""
    return pd.DataFrame(
        {
            "id_municipio": ["3550308", "3304557", "2927408", "1100205"],
            "nome": ["  São Paulo ", "Rio de Janeiro", "Salvador", " Porto Velho"],
            "sigla_uf": ["sp", "RJ", "ba", "ro"],
            "_ingestion_id": ["ing-1"] * 4,
            "_ingestion_timestamp": ["2026-07-13T00:00:00+00:00"] * 4,
            "_source_table": ["basedosdados.br_bd_diretorios_brasil.municipio"] * 4,
            "_load_type": ["BATCH"] * 4,
            "_record_hash": ["h1", "h2", "h3", "h4"],
        }
    )

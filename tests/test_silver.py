"""Testes da materialização Silver de municípios (quarentena e auditoria)."""

from __future__ import annotations

import pandas as pd

from src.common.io_utils import read_parquet_dir
from src.quality.rules.municipio import build_municipio_spec
from src.silver.loader import build_silver
from src.silver.transform import SILVER_METADATA_COLUMNS


def test_silver_valid_and_quarantine(settings, municipio_bronze):
    # Injeta um registro inválido (UF inexistente).
    bad = municipio_bronze.copy()
    bad.loc[1, "sigla_uf"] = "XX"

    loaded = {}

    def fake_bq_loader(df: pd.DataFrame, entity: str) -> int:
        loaded["count"] = len(df)
        return len(df)

    result = build_silver(
        settings,
        "municipio",
        bad,
        build_municipio_spec(),
        bq_loader=fake_bq_loader,
    )

    # Invariantes de contagem.
    assert result.bronze_count == 4
    assert result.valid_count + result.invalid_count == result.bronze_count
    assert result.invalid_count == 1
    assert result.silver_loaded_count == result.valid_count
    assert loaded["count"] == result.valid_count

    # Silver gravada com metadados obrigatórios.
    silver_df = read_parquet_dir(settings.silver_path / "municipio")
    for column in SILVER_METADATA_COLUMNS:
        assert column in silver_df.columns
    assert (silver_df["_quality_status"] == "VALID").all()

    # Quarentena criada.
    quarantine_df = read_parquet_dir(settings.quarantine_path / "municipio")
    assert len(quarantine_df) == 1
    assert (quarantine_df["_quality_status"] == "INVALID").all()


def test_quality_report_is_written(settings, municipio_bronze):
    result = build_silver(
        settings, "municipio", municipio_bronze, build_municipio_spec()
    )
    report_dir = settings.audit_path / "quality" / "municipio"
    reports = list(report_dir.glob("*.json"))
    assert len(reports) == 1
    quality_results = settings.audit_path / "quality_results.jsonl"
    assert quality_results.exists()
    assert result.valid_count == 4

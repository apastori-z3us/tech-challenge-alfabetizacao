"""Testes do framework genérico de ingestão Batch (offline)."""

from __future__ import annotations

import pandas as pd

from src.batch.extractor import METADATA_COLUMNS, CallableReader, extract_to_bronze
from src.batch.queries import build_query
from src.batch.registry import enabled_sources, get_source, load_sources
from src.batch.runner import derive_uf_from_municipio, reader_for, run_batch_source
from src.common.io_utils import read_parquet_dir


def test_registry_loads_and_filters_enabled(settings):
    sources = load_sources(settings)
    assert "municipio" in sources
    assert sources["municipio"].enabled is True
    assert sources["meta_brasil"].enabled is False
    enabled = enabled_sources(settings)
    assert "municipio" in enabled
    assert "meta_brasil" not in enabled


def test_build_query_uses_versioned_sql_file(settings):
    source = get_source(settings, "municipio")
    sql = build_query(settings, source)
    assert "br_bd_diretorios_brasil.municipio" in sql


def test_extract_to_bronze_adds_metadata(settings):
    source = get_source(settings, "municipio")

    def fake_fetch(_settings, _source) -> pd.DataFrame:
        return pd.DataFrame(
            {
                "id_municipio": ["3550308", "3304557"],
                "nome": ["São Paulo", "Rio de Janeiro"],
                "sigla_uf": ["SP", "RJ"],
            }
        )

    result = extract_to_bronze(settings, source, CallableReader(fake_fetch))
    assert result.records_read == 2
    written = read_parquet_dir(settings.bronze_path / "batch" / "municipio")
    for column in METADATA_COLUMNS:
        assert column in written.columns
    assert written["_load_type"].eq("BATCH").all()
    assert written["_record_hash"].notna().all()
    assert written["_schema_version"].eq("1.0").all()


def test_derive_uf_returns_27_ufs(settings):
    source = get_source(settings, "uf")
    df = derive_uf_from_municipio(settings, source)
    assert len(df) == 27
    assert set(df.columns) == {"codigo_uf", "sigla_uf", "nome", "regiao"}
    assert df["sigla_uf"].is_unique


def test_run_batch_source_uf_derived(settings):
    source = get_source(settings, "uf")
    loaded = {}

    def fake_loader(df: pd.DataFrame, entity: str) -> int:
        loaded[entity] = len(df)
        return len(df)

    result = run_batch_source(
        settings, "uf", reader_for(settings, source), bronze_loader=fake_loader
    )
    assert result.records_read == 27
    assert result.bronze_loaded_count == 27
    assert loaded["uf"] == 27

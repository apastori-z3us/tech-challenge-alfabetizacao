"""Testes do framework genérico de ingestão Batch (offline)."""

from __future__ import annotations

import pandas as pd

from src.batch.extractor import METADATA_COLUMNS, CallableReader, extract_to_bronze
from src.batch.queries import build_query
from src.batch.registry import enabled_sources, get_source, load_sources
from src.batch.runner import run_batch_source
from src.common.io_utils import read_parquet_dir


def test_registry_loads_and_filters_enabled(settings):
    sources = load_sources(settings)
    assert "municipio" in sources
    assert sources["municipio"].enabled is True
    # Todas as fontes obrigatórias foram validadas e habilitadas.
    assert sources["meta_brasil"].enabled is True
    enabled = enabled_sources(settings)
    assert {"municipio", "uf", "meta_brasil", "meta_uf", "meta_municipio",
            "indicador_alfabetizacao", "aluno"}.issubset(set(enabled))


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


def test_uf_source_is_real_bigquery(settings):
    source = get_source(settings, "uf")
    assert source.enabled is True
    assert source.ingestion_type == "batch"
    assert source.table_id == "basedosdados.br_bd_diretorios_brasil.uf"


def test_run_batch_source_uf_with_injected_reader(settings, fake_reader):
    loaded = {}

    def fake_loader(df: pd.DataFrame, entity: str) -> int:
        loaded[entity] = len(df)
        return len(df)

    result = run_batch_source(
        settings, "uf", fake_reader, bronze_loader=fake_loader
    )
    assert result.records_read == 27
    assert result.bronze_loaded_count == 27
    assert loaded["uf"] == 27

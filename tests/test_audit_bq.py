"""Testes da sincronização de auditoria para BigQuery (parte pura)."""

from __future__ import annotations

import pandas as pd

from src.common.audit_bq import _flatten, _read_jsonl, sync_audit_tables


def test_flatten_serializes_nested():
    df = pd.DataFrame(
        {"a": [1, 2], "nested": [{"x": 1}, {"y": [1, 2]}], "s": ["p", "q"]}
    )
    out = _flatten(df)
    assert out["nested"].apply(lambda v: isinstance(v, str)).all()
    assert out["a"].tolist() == [1, 2]  # colunas escalares intactas


def test_read_jsonl_missing_returns_empty(tmp_path):
    assert _read_jsonl(tmp_path / "nao_existe.jsonl") == []


def test_sync_audit_tables_with_fake_client(settings):
    # Cria auditorias locais.
    from src.common.audit import PipelineRun, record_pipeline_run

    record_pipeline_run(
        settings,
        PipelineRun(pipeline_name="x", source="s", layer="bronze", status="SUCCESS"),
    )

    calls = {}

    class FakeResult:
        records_loaded = 1

    def fake_load(client, s, df, table, layer="audit"):
        calls[table] = len(df)
        return FakeResult()

    import src.bronze.loader as loader_mod

    original = loader_mod.load_dataframe_to_bigquery
    loader_mod.load_dataframe_to_bigquery = fake_load
    try:
        loaded = sync_audit_tables(object(), settings)
    finally:
        loader_mod.load_dataframe_to_bigquery = original

    assert loaded.get("pipeline_runs") == 1
    assert calls["pipeline_runs"] == 1

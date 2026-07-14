"""Teste ponta a ponta local (offline) com a entidade UF derivada."""

from __future__ import annotations

import argparse

import pytest

from scripts.generate_monitoring_report import build_report
from src.cli import cmd_batch, cmd_gold, cmd_silver, cmd_validate_config

pytestmark = pytest.mark.e2e


def test_full_pipeline_uf(settings):
    assert cmd_validate_config(settings, argparse.Namespace()) == 0
    assert cmd_batch(settings, argparse.Namespace(source="uf")) == 0
    assert cmd_silver(settings, argparse.Namespace(entity="uf")) == 0
    assert cmd_gold(settings, argparse.Namespace()) == 0

    # Bronze, Silver e auditoria materializadas.
    assert list((settings.bronze_path / "batch" / "uf").rglob("*.parquet"))
    assert list((settings.silver_path / "uf").rglob("*.parquet"))
    assert (settings.audit_path / "pipeline_runs.jsonl").exists()

    report = build_report(settings)
    assert report["registros_validos"] >= 27
    assert report["taxa_rejeicao_pct"] == 0.0

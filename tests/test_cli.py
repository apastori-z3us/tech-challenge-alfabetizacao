"""Testes da CLI de orquestração e do relatório de monitoramento."""

from __future__ import annotations

import argparse

from scripts.generate_monitoring_report import build_report
from src.cli import (
    build_parser,
    cmd_batch,
    cmd_gold,
    cmd_silver,
    cmd_validate_config,
)


def test_parser_requires_command():
    parser = build_parser()
    ns = parser.parse_args(["batch", "--source", "uf"])
    assert ns.command == "batch"
    assert ns.source == "uf"


def test_validate_config(settings):
    assert cmd_validate_config(settings, argparse.Namespace()) == 0


def test_batch_silver_gold_uf_offline(settings, fake_reader):
    assert cmd_batch(settings, argparse.Namespace(source="uf"), fake_reader) == 0
    assert (settings.bronze_path / "batch" / "uf").exists()

    assert cmd_silver(settings, argparse.Namespace(entity="uf")) == 0
    assert (settings.silver_path / "uf").exists()

    assert cmd_gold(settings, argparse.Namespace()) == 0


def test_monitoring_report_after_run(settings, fake_reader):
    cmd_batch(settings, argparse.Namespace(source="uf"), fake_reader)
    cmd_silver(settings, argparse.Namespace(entity="uf"))
    report = build_report(settings)
    assert report["total_pipeline_runs"] >= 1
    assert "uf" in report["entidades_processadas"]
    assert report["registros_validos"] >= 27

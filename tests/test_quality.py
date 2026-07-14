"""Testes das regras de qualidade de municípios."""

from __future__ import annotations

import pandas as pd
import pytest

from src.quality.checks import run_quality
from src.quality.models import CriticalSchemaError
from src.quality.rules.municipio import build_municipio_spec


def _base_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "id_municipio": ["3550308", "3304557"],
            "nome": ["  São Paulo ", "Rio de Janeiro"],
            "sigla_uf": ["sp", "RJ"],
        }
    )


def test_valid_records_pass():
    report = run_quality(_base_df(), build_municipio_spec())
    assert report.total_read == 2
    assert report.valid_count == 2
    assert report.invalid_count == 0
    assert report.status == "PASSED"


def test_text_is_standardized():
    report = run_quality(_base_df(), build_municipio_spec())
    row = report.valid_df.iloc[0]
    assert row["nome"] == "São Paulo"  # espaços removidos
    assert row["sigla_uf"] == "SP"  # UF em maiúsculo


def test_invalid_uf_is_rejected():
    df = _base_df()
    df.loc[0, "sigla_uf"] = "XX"
    report = run_quality(df, build_municipio_spec())
    assert report.invalid_count == 1
    assert report.failures_by_rule.get("sigla_uf.valid_uf") == 1


def test_invalid_code_is_rejected():
    df = _base_df()
    df.loc[0, "id_municipio"] = "355"  # menos de 7 dígitos
    report = run_quality(df, build_municipio_spec())
    assert report.invalid_count == 1
    assert report.failures_by_rule.get("id_municipio.seven_digits") == 1


def test_duplicates_are_rejected():
    df = pd.concat([_base_df(), _base_df().iloc[[0]]], ignore_index=True)
    report = run_quality(df, build_municipio_spec())
    assert report.total_read == 3
    assert report.invalid_count == 1
    assert any(r.startswith("unique.") for r in report.failures_by_rule)


def test_missing_required_column_raises():
    df = _base_df().drop(columns=["sigla_uf"])
    with pytest.raises(CriticalSchemaError):
        run_quality(df, build_municipio_spec())


def test_null_name_is_rejected():
    df = _base_df()
    df.loc[0, "nome"] = "   "
    report = run_quality(df, build_municipio_spec())
    assert report.invalid_count == 1
    assert report.failures_by_rule.get("nome.not_null") == 1

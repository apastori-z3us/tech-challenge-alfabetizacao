"""Testes de integração/integridade referencial (Fase 5)."""

from __future__ import annotations

import pandas as pd

from src.gold.integration import (
    anti_join,
    incompatible_years,
    integrity_report,
    match_percentage,
)


def _municipio() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "id_municipio": ["3550308", "3304557", "9999999"],
            "nome": ["São Paulo", "Rio de Janeiro", "Fantasma"],
            "sigla_uf": ["SP", "RJ", "ZZ"],  # ZZ é UF inexistente
        }
    )


def _uf() -> pd.DataFrame:
    return pd.DataFrame(
        {"codigo_uf": ["35", "33"], "sigla_uf": ["SP", "RJ"], "nome": ["SP", "RJ"]}
    )


def test_orphan_municipio_detected():
    orphans = anti_join(_municipio(), _uf(), ["sigla_uf"])
    assert len(orphans) == 1
    assert orphans.iloc[0]["sigla_uf"] == "ZZ"


def test_match_percentage():
    pct = match_percentage(_municipio(), _uf(), ["sigla_uf"])
    assert pct == round(200 / 3, 2)


def test_incompatible_years():
    indicador = pd.DataFrame({"ano": [2020, 2023], "id_municipio": ["1", "2"]})
    meta = pd.DataFrame({"ano": [2023], "id_municipio": ["2"]})
    assert incompatible_years(indicador, meta) == [2020]


def test_integrity_report():
    report = integrity_report(municipio=_municipio(), uf=_uf())
    assert report["municipios_orfaos"] == 1
    assert report["municipio_chaves_duplicadas"] == 0

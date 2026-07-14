"""Testes dos produtos analíticos da camada Gold."""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.gold.build import (
    STATUS_ATINGIDA,
    STATUS_NAO_ATINGIDA,
    STATUS_SEM_META,
    evolucao_temporal,
    indicador_municipio_ano,
    meta_vs_resultado,
    ml_features_municipio,
    resumo_uf,
)


def _municipio() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "id_municipio": ["3550308", "3304557", "2927408"],
            "nome": ["São Paulo", "Rio de Janeiro", "Salvador"],
            "sigla_uf": ["SP", "RJ", "BA"],
        }
    )


def _indicador() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "ano": [2023, 2023, 2023],
            "id_municipio": ["3550308", "3304557", "2927408"],
            "taxa_alfabetizacao": [90.0, 70.0, 60.0],
        }
    )


def _meta_municipio() -> pd.DataFrame:
    # Salvador (2927408) sem meta -> SEM_META
    return pd.DataFrame(
        {
            "ano": [2023, 2023],
            "id_municipio": ["3550308", "3304557"],
            "valor_meta": [85.0, 80.0],
        }
    )


def test_indicador_municipio_ano_status():
    p1 = indicador_municipio_ano(_indicador(), _meta_municipio(), _municipio())
    by_id = p1.set_index("id_municipio")
    assert by_id.loc["3550308", "status_meta"] == STATUS_ATINGIDA  # 90 >= 85
    assert by_id.loc["3304557", "status_meta"] == STATUS_NAO_ATINGIDA  # 70 < 80
    assert by_id.loc["2927408", "status_meta"] == STATUS_SEM_META
    assert by_id.loc["3550308", "regiao"] == "Sudeste"


def test_percentual_atingimento_handles_zero_meta():
    meta = _meta_municipio().copy()
    meta.loc[0, "valor_meta"] = 0.0
    p1 = indicador_municipio_ano(_indicador(), meta, _municipio())
    val = p1.set_index("id_municipio").loc["3550308", "percentual_atingimento"]
    assert pd.isna(val)  # divisão por zero tratada


def test_evolucao_temporal_variacao():
    ind = pd.DataFrame(
        {
            "ano": [2021, 2022, 2023],
            "id_municipio": ["3550308"] * 3,
            "taxa_alfabetizacao": [80.0, 85.0, 90.0],
        }
    )
    evo = evolucao_temporal(ind).sort_values("ano").reset_index(drop=True)
    assert evo.loc[0, "variacao_anual"] != evo.loc[0, "variacao_anual"] or pd.isna(
        evo.loc[0, "variacao_anual"]
    )
    assert evo.loc[1, "variacao_anual"] == 5.0
    assert evo.loc[2, "variacao_acumulada"] == 10.0


def test_resumo_uf_counts():
    p1 = indicador_municipio_ano(_indicador(), _meta_municipio(), _municipio())
    resumo = resumo_uf(p1, pd.DataFrame()).set_index("sigla_uf")
    assert resumo.loc["SP", "qtd_municipios"] == 1
    assert resumo.loc["SP", "municipios_atingiram_meta"] == 1
    assert resumo.loc["SP", "percentual_atingiu"] == 100.0


def test_meta_vs_resultado_and_ml_features():
    p1 = indicador_municipio_ano(_indicador(), _meta_municipio(), _municipio())
    meta_uf = pd.DataFrame(
        {"ano": [2023], "sigla_uf": ["SP"], "valor_meta": [88.0]}
    )
    meta_brasil = pd.DataFrame({"ano": [2023], "valor_meta": [82.0]})
    mvr = meta_vs_resultado(p1, meta_uf, meta_brasil).set_index("id_municipio")
    assert np.isclose(mvr.loc["3550308", "dif_abs_estadual"], 2.0)
    assert np.isclose(mvr.loc["3550308", "dif_abs_nacional"], 8.0)

    evo = evolucao_temporal(_indicador())
    feats = ml_features_municipio(p1, evo)
    assert "atingiu_meta" in feats.columns
    assert set(feats["atingiu_meta"].dropna().unique()).issubset({0, 1})

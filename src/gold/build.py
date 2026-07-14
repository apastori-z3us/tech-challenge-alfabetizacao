"""Produtos analíticos da camada Gold (Fase 6).

Todas as funções são puras (pandas → pandas), tratam divisão por zero e dados
ausentes e não expõem dados pessoais. Os produtos só são materializados com dados
reais e integrações válidas; com fontes ausentes, servem-se de fixtures nos testes.
"""

from __future__ import annotations

from datetime import date

import numpy as np
import pandas as pd

from src.quality.reference import UF_TO_REGIAO

STATUS_ATINGIDA = "ATINGIDA"
STATUS_NAO_ATINGIDA = "NAO_ATINGIDA"
STATUS_SEM_META = "SEM_META"
STATUS_SEM_RESULTADO = "SEM_RESULTADO"


def _safe_ratio(numerator: pd.Series, denominator: pd.Series) -> pd.Series:
    """Divisão protegida contra zero/NaN (retorna NaN onde indefinido)."""
    denom = denominator.replace(0, np.nan)
    return numerator / denom


def _status_meta(taxa: float, meta: float) -> str:
    if pd.isna(meta):
        return STATUS_SEM_META
    if pd.isna(taxa):
        return STATUS_SEM_RESULTADO
    return STATUS_ATINGIDA if taxa >= meta else STATUS_NAO_ATINGIDA


def indicador_municipio_ano(
    indicador: pd.DataFrame,
    meta_municipio: pd.DataFrame,
    municipio: pd.DataFrame,
) -> pd.DataFrame:
    """Produto 1: indicador por município e ano vs. meta municipal."""
    base = indicador[["ano", "id_municipio", "taxa_alfabetizacao"]].copy()
    base["ano"] = pd.to_numeric(base["ano"], errors="coerce").astype("Int64")
    base["taxa_alfabetizacao"] = pd.to_numeric(
        base["taxa_alfabetizacao"], errors="coerce"
    )

    dim = municipio[["id_municipio", "nome", "sigla_uf"]].rename(
        columns={"nome": "nome_municipio"}
    )
    result = base.merge(dim, on="id_municipio", how="left")
    result["regiao"] = result["sigla_uf"].map(UF_TO_REGIAO)

    if not meta_municipio.empty:
        meta = meta_municipio[["ano", "id_municipio", "valor_meta"]].copy()
        meta["ano"] = pd.to_numeric(meta["ano"], errors="coerce").astype("Int64")
        meta["valor_meta"] = pd.to_numeric(meta["valor_meta"], errors="coerce")
        meta = meta.rename(columns={"valor_meta": "meta_municipal"})
        result = result.merge(meta, on=["ano", "id_municipio"], how="left")
    else:
        result["meta_municipal"] = np.nan

    result["diferenca_meta"] = (
        result["taxa_alfabetizacao"] - result["meta_municipal"]
    )
    result["percentual_atingimento"] = (
        _safe_ratio(result["taxa_alfabetizacao"], result["meta_municipal"]) * 100
    ).round(2)
    result["status_meta"] = [
        _status_meta(t, m)
        for t, m in zip(
            result["taxa_alfabetizacao"], result["meta_municipal"], strict=False
        )
    ]
    result["data_atualizacao"] = date.today().isoformat()
    return result[
        [
            "ano", "id_municipio", "nome_municipio", "sigla_uf", "regiao",
            "taxa_alfabetizacao", "meta_municipal", "diferenca_meta",
            "percentual_atingimento", "status_meta", "data_atualizacao",
        ]
    ]


def meta_vs_resultado(
    produto1: pd.DataFrame,
    meta_uf: pd.DataFrame,
    meta_brasil: pd.DataFrame,
) -> pd.DataFrame:
    """Produto 2: compara resultado com metas municipal, estadual e nacional."""
    result = produto1.copy()

    if not meta_uf.empty:
        muf = meta_uf[["ano", "sigla_uf", "valor_meta"]].copy()
        muf["ano"] = pd.to_numeric(muf["ano"], errors="coerce").astype("Int64")
        muf = muf.rename(columns={"valor_meta": "meta_estadual"})
        result = result.merge(muf, on=["ano", "sigla_uf"], how="left")
    else:
        result["meta_estadual"] = np.nan

    if not meta_brasil.empty:
        mbr = meta_brasil[["ano", "valor_meta"]].copy()
        mbr["ano"] = pd.to_numeric(mbr["ano"], errors="coerce").astype("Int64")
        mbr = mbr.rename(columns={"valor_meta": "meta_nacional"})
        result = result.merge(mbr, on="ano", how="left")
    else:
        result["meta_nacional"] = np.nan

    result["dif_abs_municipal"] = result["diferenca_meta"]
    result["dif_pct_municipal"] = result["percentual_atingimento"]
    result["dif_abs_estadual"] = (
        result["taxa_alfabetizacao"] - result["meta_estadual"]
    )
    result["dif_abs_nacional"] = (
        result["taxa_alfabetizacao"] - result["meta_nacional"]
    )
    return result[
        [
            "ano", "id_municipio", "sigla_uf", "taxa_alfabetizacao",
            "meta_municipal", "meta_estadual", "meta_nacional",
            "dif_abs_municipal", "dif_pct_municipal",
            "dif_abs_estadual", "dif_abs_nacional", "status_meta",
        ]
    ]


def evolucao_temporal(
    indicador: pd.DataFrame,
    tipo_localidade: str = "municipio",
    codigo_col: str = "id_municipio",
    nome_col: str | None = None,
) -> pd.DataFrame:
    """Produto 3: evolução temporal da taxa por localidade."""
    df = indicador.copy()
    df["ano"] = pd.to_numeric(df["ano"], errors="coerce").astype("Int64")
    df["taxa_alfabetizacao"] = pd.to_numeric(
        df["taxa_alfabetizacao"], errors="coerce"
    )
    df = df.sort_values([codigo_col, "ano"]).reset_index(drop=True)

    grp = df.groupby(codigo_col, group_keys=False)
    df["taxa_ano_anterior"] = grp["taxa_alfabetizacao"].shift(1)
    df["variacao_anual"] = df["taxa_alfabetizacao"] - df["taxa_ano_anterior"]
    df["taxa_primeiro_ano"] = grp["taxa_alfabetizacao"].transform("first")
    df["variacao_acumulada"] = (
        df["taxa_alfabetizacao"] - df["taxa_primeiro_ano"]
    )

    out = pd.DataFrame(
        {
            "tipo_localidade": tipo_localidade,
            "codigo_localidade": df[codigo_col],
            "nome_localidade": df[nome_col] if nome_col else df[codigo_col],
            "ano": df["ano"],
            "taxa_alfabetizacao": df["taxa_alfabetizacao"],
            "taxa_ano_anterior": df["taxa_ano_anterior"],
            "variacao_anual": df["variacao_anual"],
            "variacao_acumulada": df["variacao_acumulada"],
        }
    )
    return out.reset_index(drop=True)


def resumo_uf(produto1: pd.DataFrame, meta_uf: pd.DataFrame) -> pd.DataFrame:
    """Produto 4: estatísticas de alfabetização agregadas por UF."""
    df = produto1.copy()
    grouped = df.groupby("sigla_uf")

    rows = []
    for sigla, g in grouped:
        com_resultado = g["taxa_alfabetizacao"].notna().sum()
        sem_resultado = g["taxa_alfabetizacao"].isna().sum()
        atingiram = (g["status_meta"] == STATUS_ATINGIDA).sum()
        total = len(g)
        rows.append(
            {
                "sigla_uf": sigla,
                "media": round(g["taxa_alfabetizacao"].mean(), 2),
                "mediana": round(g["taxa_alfabetizacao"].median(), 2),
                "minimo": g["taxa_alfabetizacao"].min(),
                "maximo": g["taxa_alfabetizacao"].max(),
                "qtd_municipios": total,
                "municipios_com_resultado": int(com_resultado),
                "municipios_sem_resultado": int(sem_resultado),
                "municipios_atingiram_meta": int(atingiram),
                "percentual_atingiu": round(100.0 * atingiram / total, 2)
                if total
                else 0.0,
            }
        )
    resumo = pd.DataFrame(rows)

    if not meta_uf.empty and not resumo.empty:
        muf = (
            meta_uf.groupby("sigla_uf")["valor_meta"]
            .mean()
            .rename("meta_estadual")
            .reset_index()
        )
        resumo = resumo.merge(muf, on="sigla_uf", how="left")
        resumo["dif_media_para_meta_estadual"] = (
            resumo["media"] - resumo["meta_estadual"]
        )
    return resumo


def ml_features_municipio(
    produto1: pd.DataFrame, evolucao: pd.DataFrame
) -> pd.DataFrame:
    """Produto 5 (opcional): atributos para IA, sem dados pessoais."""
    feats = produto1[
        [
            "ano", "id_municipio", "sigla_uf", "regiao",
            "taxa_alfabetizacao", "meta_municipal", "diferenca_meta",
        ]
    ].copy()
    var = evolucao[["ano", "codigo_localidade", "variacao_anual"]].rename(
        columns={"codigo_localidade": "id_municipio"}
    )
    feats = feats.merge(var, on=["ano", "id_municipio"], how="left")
    feats["atingiu_meta"] = (
        feats["taxa_alfabetizacao"] >= feats["meta_municipal"]
    ).astype("Int64")
    return feats

"""Integração e integridade referencial entre as entidades (Fase 5).

Funções puras de pandas que validam relacionamentos, isolam registros órfãos e
medem o percentual de correspondência antes de qualquer junção na Gold. Junções
só ocorrem quando chaves, granularidades e períodos são compatíveis.
"""

from __future__ import annotations

import pandas as pd


def anti_join(
    left: pd.DataFrame, right: pd.DataFrame, keys: list[str]
) -> pd.DataFrame:
    """Registros de `left` sem correspondência em `right` pelas `keys`."""
    present = [k for k in keys if k in left.columns and k in right.columns]
    if not present:
        return left.copy()
    merged = left.merge(
        right[present].drop_duplicates(), on=present, how="left", indicator=True
    )
    orphans = merged[merged["_merge"] == "left_only"].drop(columns="_merge")
    return orphans.reset_index(drop=True)


def match_percentage(
    left: pd.DataFrame, right: pd.DataFrame, keys: list[str]
) -> float:
    """Percentual de linhas de `left` com correspondência em `right`."""
    if left.empty:
        return 0.0
    orphans = anti_join(left, right, keys)
    matched = len(left) - len(orphans)
    return round(100.0 * matched / len(left), 2)


def duplicated_keys(dataframe: pd.DataFrame, keys: list[str]) -> pd.DataFrame:
    """Linhas com chave duplicada."""
    present = [k for k in keys if k in dataframe.columns]
    if not present:
        return dataframe.iloc[0:0]
    mask = dataframe.duplicated(subset=present, keep=False)
    return dataframe[mask].reset_index(drop=True)


def incompatible_years(
    left: pd.DataFrame, right: pd.DataFrame, year_col: str = "ano"
) -> list:
    """Anos presentes em `left` que não existem em `right` (não comparáveis)."""
    if year_col not in left.columns or year_col not in right.columns:
        return []
    left_years = set(pd.to_numeric(left[year_col], errors="coerce").dropna())
    right_years = set(pd.to_numeric(right[year_col], errors="coerce").dropna())
    return sorted(int(y) for y in (left_years - right_years))


def integrity_report(
    *,
    municipio: pd.DataFrame,
    uf: pd.DataFrame,
    meta_municipio: pd.DataFrame | None = None,
    indicador: pd.DataFrame | None = None,
) -> dict:
    """Consolida os principais indicadores de integridade referencial."""
    meta_municipio = (
        meta_municipio if meta_municipio is not None else pd.DataFrame()
    )
    indicador = indicador if indicador is not None else pd.DataFrame()

    municipios_orfaos = anti_join(municipio, uf, ["sigla_uf"])

    metas_sem_municipio = (
        anti_join(meta_municipio, municipio, ["id_municipio"])
        if not meta_municipio.empty
        else pd.DataFrame()
    )
    resultados_sem_meta = (
        anti_join(indicador, meta_municipio, ["ano", "id_municipio"])
        if not indicador.empty and not meta_municipio.empty
        else pd.DataFrame()
    )

    return {
        "municipios_orfaos": len(municipios_orfaos),
        "municipio_uf_match_pct": match_percentage(municipio, uf, ["sigla_uf"]),
        "metas_sem_municipio": len(metas_sem_municipio),
        "resultados_sem_meta": len(resultados_sem_meta),
        "anos_incompativeis_indicador_meta": incompatible_years(
            indicador, meta_municipio
        )
        if not indicador.empty and not meta_municipio.empty
        else [],
        "municipio_chaves_duplicadas": len(
            duplicated_keys(municipio, ["id_municipio"])
        ),
    }

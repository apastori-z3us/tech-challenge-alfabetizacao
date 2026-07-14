"""Orquestração da camada Gold a partir da Silver local (Parquet)."""

from __future__ import annotations

import pandas as pd

from src.common.io_utils import partition_dir, write_parquet
from src.common.logger import configure_logger
from src.common.settings import Settings, processing_date
from src.gold.build import (
    evolucao_temporal,
    indicador_municipio_ano,
    meta_vs_resultado,
    ml_features_municipio,
    resumo_uf,
)
from src.gold.integration import integrity_report


def _read_silver(settings: Settings, entity: str) -> pd.DataFrame:
    directory = settings.silver_path / entity
    if not directory.exists():
        return pd.DataFrame()
    try:
        from src.common.io_utils import read_latest_parquet

        return read_latest_parquet(directory)
    except FileNotFoundError:
        return pd.DataFrame()


def _write_gold(
    settings: Settings, name: str, frame: pd.DataFrame, gold_loader=None
) -> str | None:
    if frame.empty:
        return None
    directory = partition_dir(
        settings.gold_path, name, "processing_date", processing_date()
    )
    path = directory / f"{name}.parquet"
    write_parquet(frame, path)
    if gold_loader is not None:
        loaded = gold_loader(frame, name)
        return f"{path} | BQ={loaded} linhas"
    return str(path)


def build_gold_products(settings: Settings, *, gold_loader=None) -> dict:
    """Constrói os produtos Gold com os dados Silver disponíveis."""
    logger = configure_logger(name="gold_runner", level=settings.log_level)

    municipio = _read_silver(settings, "municipio")
    uf = _read_silver(settings, "uf")
    meta_municipio = _read_silver(settings, "meta_municipio")
    meta_uf = _read_silver(settings, "meta_uf")
    meta_brasil = _read_silver(settings, "meta_brasil")
    indicador = _read_silver(settings, "indicador_alfabetizacao")

    outputs: dict[str, str | None] = {}

    if not municipio.empty and not uf.empty:
        report = integrity_report(
            municipio=municipio,
            uf=uf,
            meta_municipio=meta_municipio,
            indicador=indicador,
        )
        logger.info("Integridade: %s", report)
        outputs["integrity"] = report

    if not indicador.empty and not municipio.empty:
        p1 = indicador_municipio_ano(indicador, meta_municipio, municipio)
        outputs["indicador_municipio_ano"] = _write_gold(
            settings, "indicador_municipio_ano", p1, gold_loader
        )
        outputs["meta_vs_resultado"] = _write_gold(
            settings, "meta_vs_resultado",
            meta_vs_resultado(p1, meta_uf, meta_brasil), gold_loader
        )
        evo = evolucao_temporal(indicador)
        outputs["evolucao_temporal"] = _write_gold(
            settings, "evolucao_temporal", evo, gold_loader
        )
        outputs["resumo_uf"] = _write_gold(
            settings, "resumo_uf", resumo_uf(p1, meta_uf), gold_loader
        )
        outputs["ml_features_municipio"] = _write_gold(
            settings, "ml_features_municipio",
            ml_features_municipio(p1, evo), gold_loader
        )
    else:
        logger.warning(
            "Gold analítica de indicador requer Silver de indicador+municipio "
            "(indisponível offline — ver docs/blockers.md)."
        )

    return outputs

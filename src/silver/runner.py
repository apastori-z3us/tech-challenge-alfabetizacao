"""Orquestração da Silver a partir da Bronze local (Parquet)."""

from __future__ import annotations

from src.common.io_utils import read_latest_parquet
from src.common.logger import configure_logger
from src.common.settings import Settings
from src.quality.rules import get_spec
from src.silver.loader import SilverResult, build_silver


def run_silver_from_bronze(
    settings: Settings, entity: str, *, bq_loader=None
) -> SilverResult | None:
    """Lê a Bronze local de uma entidade e materializa a Silver.

    Retorna None quando não há Bronze disponível para a entidade.
    """
    logger = configure_logger(name="silver_runner", level=settings.log_level)
    bronze_dir = settings.bronze_path / "batch" / entity
    if not bronze_dir.exists():
        logger.warning(
            "Sem Bronze local para '%s' em %s — etapa Silver ignorada.",
            entity,
            bronze_dir,
        )
        return None

    bronze_df = read_latest_parquet(bronze_dir)
    spec = get_spec(entity)
    return build_silver(settings, entity, bronze_df, spec, bq_loader=bq_loader)

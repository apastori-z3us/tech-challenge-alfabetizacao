from __future__ import annotations

from src.batch.extract import extract_municipios_to_bronze
from src.bronze.loader import load_municipios_to_bigquery
from src.common.bigquery_client import create_bigquery_client
from src.common.logger import configure_logger
from src.common.settings import load_settings


def create_local_directories() -> None:
    """Garante que todas as pastas locais necessárias existam."""

    settings = load_settings()

    directories = [
        settings.bronze_path / "batch",
        settings.bronze_path / "streaming",
        settings.silver_path,
        settings.gold_path,
        settings.audit_path,
        settings.quarantine_path,
    ]

    for directory in directories:
        directory.mkdir(
            parents=True,
            exist_ok=True,
        )


def run_municipio_bronze_pipeline() -> None:
    """
    Executa o primeiro fluxo funcional:

    Base dos Dados -> Parquet local -> Bronze BigQuery.
    """

    settings = load_settings()

    logger = configure_logger(
        name="municipio_pipeline",
        level=settings.log_level,
    )

    logger.info(
        "Iniciando pipeline de municípios."
    )

    logger.info(
        "Projeto Google Cloud: %s",
        settings.google_cloud_project,
    )

    create_local_directories()

    client = create_bigquery_client(settings)

    extraction_result = extract_municipios_to_bronze(
        client=client,
        settings=settings,
    )

    load_result = load_municipios_to_bigquery(
        client=client,
        settings=settings,
        dataframe=extraction_result.dataframe,
    )

    if (
        extraction_result.records_read
        != load_result.records_loaded
    ):
        raise RuntimeError(
            "A quantidade extraída é diferente da quantidade "
            "carregada no BigQuery. "
            f"Extraídos={extraction_result.records_read}, "
            f"carregados={load_result.records_loaded}."
        )

    logger.info(
        "Pipeline finalizado com sucesso."
    )

    logger.info(
        "Arquivo Parquet: %s",
        extraction_result.output_path,
    )

    logger.info(
        "Tabela BigQuery: %s",
        load_result.table_id,
    )

    logger.info(
        "Registros processados: %s",
        load_result.records_loaded,
    )


def main() -> None:
    try:
        run_municipio_bronze_pipeline()
    except Exception:
        logger = configure_logger(
            name="municipio_pipeline",
        )

        logger.exception(
            "O pipeline foi encerrado com erro."
        )

        raise


if __name__ == "__main__":
    main()
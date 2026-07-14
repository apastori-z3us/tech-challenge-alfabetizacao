from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
from google.cloud import bigquery

from src.common.logger import configure_logger
from src.common.settings import Settings


@dataclass
class BigQueryLoadResult:
    """Resultado do carregamento de uma tabela no BigQuery."""

    table_id: str
    records_loaded: int
    job_id: str


def load_municipios_to_bigquery(
    client: bigquery.Client,
    settings: Settings,
    dataframe: pd.DataFrame,
) -> BigQueryLoadResult:
    """
    Carrega o DataFrame de municípios na camada Bronze
    do BigQuery.
    """

    logger = configure_logger(
        name="bronze_loader",
        level=settings.log_level,
    )

    table_id = (
        f"{settings.google_cloud_project}."
        f"{settings.dataset_bronze}."
        "municipio"
    )

    schema = [
        bigquery.SchemaField(
            "id_municipio",
            "STRING",
            mode="REQUIRED",
        ),
        bigquery.SchemaField(
            "nome",
            "STRING",
            mode="NULLABLE",
        ),
        bigquery.SchemaField(
            "sigla_uf",
            "STRING",
            mode="NULLABLE",
        ),
        bigquery.SchemaField(
            "_ingestion_id",
            "STRING",
            mode="REQUIRED",
        ),
        bigquery.SchemaField(
            "_ingestion_timestamp",
            "TIMESTAMP",
            mode="REQUIRED",
        ),
        bigquery.SchemaField(
            "_source_table",
            "STRING",
            mode="REQUIRED",
        ),
        bigquery.SchemaField(
            "_load_type",
            "STRING",
            mode="REQUIRED",
        ),
        bigquery.SchemaField(
            "_record_hash",
            "STRING",
            mode="REQUIRED",
        ),
    ]

    job_config = bigquery.LoadJobConfig(
        schema=schema,
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
        create_disposition=bigquery.CreateDisposition.CREATE_IF_NEEDED,
    )

    logger.info(
        "Iniciando carregamento no BigQuery. tabela=%s",
        table_id,
    )

    load_job = client.load_table_from_dataframe(
        dataframe=dataframe,
        destination=table_id,
        job_config=job_config,
        location=settings.bigquery_location,
    )

    load_job.result()

    destination_table = client.get_table(table_id)

    logger.info(
        "Carregamento concluído. tabela=%s | registros=%s",
        table_id,
        destination_table.num_rows,
    )

    return BigQueryLoadResult(
        table_id=table_id,
        records_loaded=destination_table.num_rows,
        job_id=load_job.job_id,
    )
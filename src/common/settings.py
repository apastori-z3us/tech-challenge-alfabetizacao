from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENV_FILE = PROJECT_ROOT / ".env"

load_dotenv(ENV_FILE)


def get_required_env(name: str) -> str:
    """Retorna uma variável obrigatória ou interrompe a execução."""
    value = os.getenv(name)

    if not value:
        raise RuntimeError(
            f"A variável de ambiente obrigatória '{name}' não foi configurada."
        )

    return value


def _get_int_env(name: str, default: int) -> int:
    """Lê uma variável inteira, com valor padrão seguro."""
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    try:
        return int(raw)
    except ValueError as error:
        raise RuntimeError(
            f"A variável '{name}' deve ser um inteiro. Valor recebido: {raw!r}."
        ) from error


@dataclass(frozen=True)
class Settings:
    google_cloud_project: str
    bigquery_location: str

    dataset_bronze: str
    dataset_silver: str
    dataset_gold: str
    dataset_audit: str

    app_environment: str
    log_level: str

    kafka_bootstrap_servers: str
    kafka_topic: str
    kafka_consumer_group: str

    streaming_batch_size: int
    streaming_batch_interval_seconds: int

    project_root: Path
    data_root: Path
    bronze_path: Path
    silver_path: Path
    gold_path: Path
    audit_path: Path
    quarantine_path: Path

    config_path: Path
    sql_path: Path

    def dataset_for_layer(self, layer: str) -> str:
        """Retorna o dataset BigQuery correspondente a uma camada."""
        mapping = {
            "bronze": self.dataset_bronze,
            "silver": self.dataset_silver,
            "gold": self.dataset_gold,
            "audit": self.dataset_audit,
        }
        if layer not in mapping:
            raise ValueError(f"Camada desconhecida: {layer!r}.")
        return mapping[layer]

    def table_ref(self, layer: str, table: str) -> str:
        """Monta a referência completa `projeto.dataset.tabela`."""
        return f"{self.google_cloud_project}.{self.dataset_for_layer(layer)}.{table}"


def processing_date() -> str:
    """Data de processamento (UTC-agnóstica) no formato YYYY-MM-DD."""
    return date.today().isoformat()


def load_settings() -> Settings:
    """Carrega as configurações do projeto a partir do ambiente."""
    data_root = PROJECT_ROOT / "data"

    return Settings(
        google_cloud_project=get_required_env("GOOGLE_CLOUD_PROJECT"),
        bigquery_location=os.getenv("BQ_LOCATION", "US"),
        dataset_bronze=get_required_env("BQ_DATASET_BRONZE"),
        dataset_silver=get_required_env("BQ_DATASET_SILVER"),
        dataset_gold=get_required_env("BQ_DATASET_GOLD"),
        dataset_audit=get_required_env("BQ_DATASET_AUDIT"),
        app_environment=os.getenv("APP_ENV", "development"),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
        kafka_bootstrap_servers=os.getenv(
            "KAFKA_BOOTSTRAP_SERVERS",
            "localhost:19092",
        ),
        kafka_topic=os.getenv("KAFKA_TOPIC", "alfabetizacao-events"),
        kafka_consumer_group=os.getenv(
            "KAFKA_CONSUMER_GROUP",
            "alfabetizacao-consumer",
        ),
        streaming_batch_size=_get_int_env("STREAMING_BATCH_SIZE", 20),
        streaming_batch_interval_seconds=_get_int_env(
            "STREAMING_BATCH_INTERVAL_SECONDS", 10
        ),
        project_root=PROJECT_ROOT,
        data_root=data_root,
        bronze_path=data_root / "bronze",
        silver_path=data_root / "silver",
        gold_path=data_root / "gold",
        audit_path=data_root / "audit",
        quarantine_path=data_root / "quarantine",
        config_path=PROJECT_ROOT / "config",
        sql_path=PROJECT_ROOT / "sql",
    )

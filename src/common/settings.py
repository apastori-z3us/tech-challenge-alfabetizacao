from __future__ import annotations

import os
from dataclasses import dataclass
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

    project_root: Path
    data_root: Path
    bronze_path: Path
    silver_path: Path
    gold_path: Path
    audit_path: Path
    quarantine_path: Path


def load_settings() -> Settings:
    """Carrega as configurações do projeto."""
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
        kafka_topic=os.getenv(
            "KAFKA_TOPIC",
            "alfabetizacao-events",
        ),
        kafka_consumer_group=os.getenv(
            "KAFKA_CONSUMER_GROUP",
            "alfabetizacao-consumer",
        ),
        project_root=PROJECT_ROOT,
        data_root=data_root,
        bronze_path=data_root / "bronze",
        silver_path=data_root / "silver",
        gold_path=data_root / "gold",
        audit_path=data_root / "audit",
        quarantine_path=data_root / "quarantine",
    )
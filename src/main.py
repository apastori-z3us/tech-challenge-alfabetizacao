from __future__ import annotations

from src.common.bigquery_client import create_bigquery_client
from src.common.logger import configure_logger
from src.common.settings import load_settings


def create_local_directories() -> None:
    """Garante que as pastas de dados locais existam."""
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
        directory.mkdir(parents=True, exist_ok=True)


def test_bigquery_connection() -> None:
    """Executa uma consulta simples para validar o BigQuery."""
    settings = load_settings()
    logger = configure_logger(level=settings.log_level)

    client = create_bigquery_client(settings)

    query = """
        SELECT
            CURRENT_DATE() AS data_atual,
            'CONEXAO_OK' AS status
    """

    result = list(client.query(query).result())

    if not result:
        raise RuntimeError("O BigQuery não retornou resultados.")

    row = result[0]

    logger.info(
        "BigQuery conectado. Projeto=%s | Data=%s | Status=%s",
        settings.google_cloud_project,
        row["data_atual"],
        row["status"],
    )


def main() -> None:
    settings = load_settings()
    logger = configure_logger(level=settings.log_level)

    logger.info("Iniciando estrutura do Tech Challenge.")
    logger.info("Projeto Google Cloud: %s", settings.google_cloud_project)
    logger.info("Ambiente: %s", settings.app_environment)

    create_local_directories()
    logger.info("Pastas locais verificadas.")

    test_bigquery_connection()

    logger.info("Estrutura inicial validada com sucesso.")


if __name__ == "__main__":
    main()
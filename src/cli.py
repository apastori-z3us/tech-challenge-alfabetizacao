"""Interface de linha de comando do pipeline (orquestração central).

Comandos: batch, silver, gold, quality, all, stream-producer, stream-consumer,
validate-config. Projetada para operar offline (Parquet) e, quando o BigQuery
estiver acessível, também em nuvem — sem quebrar o fluxo local.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from src.batch.registry import enabled_sources, get_source, load_sources
from src.batch.runner import reader_for, run_batch_source
from src.common.audit import PipelineRun, record_pipeline_run
from src.common.logger import configure_logger
from src.common.settings import Settings, load_settings
from src.gold.runner import build_gold_products
from src.quality.rules import SPEC_BUILDERS
from src.silver.runner import run_silver_from_bronze

logger = configure_logger(name="cli")


def _bigquery_client_or_none(settings: Settings):
    """Tenta criar um cliente BigQuery; retorna None se indisponível."""
    try:
        from src.common.bigquery_client import create_bigquery_client

        client = create_bigquery_client(settings)
        client.query("SELECT 1").result()  # valida a conectividade
        return client
    except Exception as error:  # noqa: BLE001 - blocker de ambiente conhecido
        logger.warning(
            "BigQuery indisponível (%s). Etapas de nuvem serão ignoradas. "
            "Ver docs/blockers.md.",
            type(error).__name__,
        )
        return None


def cmd_validate_config(settings: Settings, _args) -> int:
    sources = load_sources(settings)
    enabled = enabled_sources(settings)
    logger.info("Fontes declaradas: %s", sorted(sources))
    logger.info("Fontes habilitadas: %s", sorted(enabled))
    logger.info("Entidades com regras de qualidade: %s", sorted(SPEC_BUILDERS))
    logger.info("Configuração válida.")
    return 0


def cmd_batch(settings: Settings, args) -> int:
    targets = (
        {args.source: get_source(settings, args.source)}
        if args.source
        else enabled_sources(settings)
    )
    # Só tenta o BigQuery se houver alguma fonte não-derivada a processar.
    needs_bq = any(s.ingestion_type != "derived" for s in targets.values())
    client = _bigquery_client_or_none(settings) if needs_bq else None

    processed = 0
    for name, source in targets.items():
        if source.ingestion_type == "derived":
            reader = reader_for(settings, source)
        elif client is not None:
            from src.batch.extractor import BigQueryReader

            reader = BigQueryReader(client)
        else:
            logger.warning(
                "Fonte '%s' requer BigQuery (indisponível) — ignorada.", name
            )
            continue
        run_batch_source(settings, name, reader)
        processed += 1
    logger.info("Batch concluído: %s fonte(s) processada(s).", processed)
    return 0


def cmd_quality(settings: Settings, args) -> int:
    return _run_silver(settings, args, quality_only=True)


def cmd_silver(settings: Settings, args) -> int:
    return _run_silver(settings, args, quality_only=False)


def _run_silver(settings: Settings, args, quality_only: bool) -> int:
    entities = [args.entity] if getattr(args, "entity", None) else list(SPEC_BUILDERS)
    any_done = False
    for entity in entities:
        if entity not in SPEC_BUILDERS:
            logger.warning("Sem regras para '%s' — ignorada.", entity)
            continue
        result = run_silver_from_bronze(settings, entity)
        if result is not None:
            any_done = True
            logger.info(
                "%s: lidos=%s válidos=%s inválidos=%s",
                entity,
                result.bronze_count,
                result.valid_count,
                result.invalid_count,
            )
    if not any_done:
        logger.warning("Nenhuma entidade com Bronze disponível foi processada.")
    return 0


def cmd_gold(settings: Settings, _args) -> int:
    outputs = build_gold_products(settings)
    logger.info("Produtos Gold: %s", {k: v for k, v in outputs.items()})
    return 0


def cmd_all(settings: Settings, args) -> int:
    logger.info("== Pipeline completo ==")
    cmd_validate_config(settings, args)
    cmd_batch(settings, argparse.Namespace(source=None))
    cmd_silver(settings, argparse.Namespace(entity=None))
    cmd_gold(settings, args)
    record_pipeline_run(
        settings,
        PipelineRun(
            pipeline_name="all", source="orchestrator", layer="all", status="SUCCESS"
        ),
    )
    logger.info("== Pipeline completo finalizado ==")
    return 0


def cmd_stream_producer(settings: Settings, args) -> int:
    from src.streaming.producer import run_producer

    source_file = Path(args.file) if args.file else None
    published = run_producer(settings, args.events, args.interval, source_file)
    logger.info("Produtor finalizado: %s evento(s).", published)
    return 0


def cmd_stream_consumer(settings: Settings, args) -> int:
    from src.streaming.consumer import consume

    stats = consume(settings, max_events=args.max_events)
    logger.info("Consumidor finalizado: %s", stats)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m src.cli",
        description="Pipeline de alfabetização (batch + streaming).",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("validate-config", help="Valida settings, fontes e regras.")

    p_batch = sub.add_parser("batch", help="Ingestão Batch → Bronze.")
    p_batch.add_argument("--source", help="Nome da fonte (padrão: todas habilitadas).")

    p_quality = sub.add_parser("quality", help="Executa apenas qualidade.")
    p_quality.add_argument("--entity", help="Entidade (padrão: todas).")

    p_silver = sub.add_parser("silver", help="Bronze → Silver com qualidade.")
    p_silver.add_argument("--entity", help="Entidade (padrão: todas).")

    sub.add_parser("gold", help="Silver → produtos analíticos Gold.")
    sub.add_parser("all", help="Executa o pipeline completo.")

    p_prod = sub.add_parser("stream-producer", help="Publica eventos no Redpanda.")
    p_prod.add_argument("--events", type=int, default=20)
    p_prod.add_argument("--interval", type=float, default=2.0)
    p_prod.add_argument("--file", help="Arquivo de eventos (JSON/JSONL).")

    p_cons = sub.add_parser("stream-consumer", help="Consome eventos do Redpanda.")
    p_cons.add_argument("--max-events", type=int, default=None)

    return parser


_COMMANDS = {
    "validate-config": cmd_validate_config,
    "batch": cmd_batch,
    "quality": cmd_quality,
    "silver": cmd_silver,
    "gold": cmd_gold,
    "all": cmd_all,
    "stream-producer": cmd_stream_producer,
    "stream-consumer": cmd_stream_consumer,
}


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    settings = load_settings()
    handler = _COMMANDS[args.command]
    return handler(settings, args)


if __name__ == "__main__":
    sys.exit(main())

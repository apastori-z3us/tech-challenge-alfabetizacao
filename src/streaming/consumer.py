"""Consumidor de eventos de streaming (Redpanda/Kafka).

O processamento por evento (`process_event`) é independente de Kafka e testável:
valida schema, deduplica, persiste válidos na Bronze de streaming e envia
inválidos/duplicados à quarentena, registrando latência e métricas.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone

from src.common.audit import record_streaming_metric
from src.common.io_utils import partition_dir, write_json
from src.common.logger import configure_logger
from src.common.settings import Settings
from src.streaming.deduplication import Deduplicator
from src.streaming.microbatch import MicroBatcher
from src.streaming.validation import event_latency_seconds, validate_event


@dataclass
class ConsumerStats:
    """Contadores de uma sessão de consumo."""

    received: int = 0
    valid: int = 0
    invalid: int = 0
    duplicates: int = 0
    flushed_batches: int = 0
    latencies: list[float] = field(default_factory=list)

    @property
    def avg_latency(self) -> float:
        return round(sum(self.latencies) / len(self.latencies), 3) if (
            self.latencies
        ) else 0.0


def _quarantine_event(settings: Settings, event: dict, reason: list[str]) -> None:
    ingestion_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    directory = partition_dir(
        settings.quarantine_path / "streaming",
        "indicador",
        "ingestion_date",
        ingestion_date,
    )
    event_id = str(event.get("event_id", "sem_id"))
    payload = {"event": event, "errors": reason}
    write_json(payload, directory / f"{event_id}.json")


def process_event(
    settings: Settings,
    event: dict,
    dedup: Deduplicator,
    microbatcher: MicroBatcher,
    stats: ConsumerStats,
) -> str:
    """Processa um evento. Retorna 'valid' | 'invalid' | 'duplicate'."""
    stats.received += 1
    ingestion_time = datetime.now(timezone.utc).isoformat()

    is_valid, errors = validate_event(event)
    if not is_valid:
        stats.invalid += 1
        _quarantine_event(settings, event, errors)
        return "invalid"

    event_id = str(event["event_id"])
    if dedup.is_duplicate(event_id):
        stats.duplicates += 1
        _quarantine_event(settings, event, ["evento duplicado"])
        return "duplicate"
    dedup.add(event_id)

    latency = event_latency_seconds(event["event_time"], ingestion_time)
    stats.latencies.append(latency)
    enriched = {**event, "_ingestion_time": ingestion_time, "_latency_s": latency}
    microbatcher.add(enriched)
    stats.valid += 1
    return "valid"


def consume(
    settings: Settings,
    max_events: int | None = None,
    poll_timeout: float = 1.0,
) -> ConsumerStats:
    """Loop de consumo real (requer broker). Confirma só após persistência."""
    from confluent_kafka import Consumer

    logger = configure_logger(name="stream_consumer", level=settings.log_level)
    consumer = Consumer(
        {
            "bootstrap.servers": settings.kafka_bootstrap_servers,
            "group.id": settings.kafka_consumer_group,
            "auto.offset.reset": "earliest",
            "enable.auto.commit": False,
        }
    )
    consumer.subscribe([settings.kafka_topic])

    dedup = Deduplicator.from_bronze(settings.bronze_path / "streaming")
    microbatcher = MicroBatcher(settings)
    stats = ConsumerStats()

    try:
        while max_events is None or stats.received < max_events:
            message = consumer.poll(poll_timeout)
            if message is None:
                if microbatcher.should_flush() and microbatcher.flush():
                    stats.flushed_batches += 1
                continue
            if message.error():
                logger.error("Erro no consumo: %s", message.error())
                continue

            event = json.loads(message.value().decode("utf-8"))
            process_event(settings, event, dedup, microbatcher, stats)

            if microbatcher.should_flush() and microbatcher.flush():
                stats.flushed_batches += 1
            consumer.commit(message)  # confirma após persistência lógica
    finally:
        if microbatcher.flush():
            stats.flushed_batches += 1
        consumer.close()

    record_streaming_metric(
        settings,
        {
            "consumed": stats.received,
            "valid": stats.valid,
            "invalid": stats.invalid,
            "duplicates": stats.duplicates,
            "flushed_batches": stats.flushed_batches,
            "avg_latency_seconds": stats.avg_latency,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )
    logger.info(
        "Consumo encerrado: recebidos=%s válidos=%s inválidos=%s duplicados=%s",
        stats.received,
        stats.valid,
        stats.invalid,
        stats.duplicates,
    )
    return stats

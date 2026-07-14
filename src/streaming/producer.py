"""Produtor de eventos de streaming (Redpanda/Kafka).

Gera eventos sintéticos de demonstração (permitido apenas para o fluxo de
streaming) ou lê um arquivo de eventos. Nunca publica dados pessoais.
"""

from __future__ import annotations

import json
import random
import time
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from src.common.logger import configure_logger
from src.common.settings import Settings
from src.quality.reference import SIGLA_TO_CODIGO_UF, UFS_VALIDAS

# Amostra municipal para demonstração (código IBGE real, sem dado pessoal).
_DEMO_MUNICIPIOS = [
    ("3550308", "SP"),
    ("3304557", "RJ"),
    ("2927408", "BA"),
    ("1100205", "RO"),
    ("5300108", "DF"),
    ("4106902", "PR"),
    ("2304400", "CE"),
    ("3106200", "MG"),
]


def generate_event(ano: int = 2026) -> dict:
    """Cria um evento sintético válido com `event_id` único."""
    codigo, sigla = random.choice(_DEMO_MUNICIPIOS)
    return {
        "event_id": str(uuid4()),
        "event_type": "indicador_atualizado",
        "codigo_municipio": codigo,
        "sigla_uf": sigla,
        "ano_referencia": ano,
        "taxa_alfabetizacao": round(random.uniform(60.0, 99.0), 1),
        "event_time": datetime.now(timezone.utc).isoformat(),
        "source": "simulador",
        "schema_version": "1.0",
    }


def generate_events(count: int) -> list[dict]:
    """Gera uma lista de eventos sintéticos válidos."""
    return [generate_event() for _ in range(count)]


def load_events_file(path: Path) -> list[dict]:
    """Lê eventos de um arquivo JSON (lista) ou JSON Lines."""
    text = path.read_text(encoding="utf-8").strip()
    if text.startswith("["):
        return json.loads(text)
    return [json.loads(line) for line in text.splitlines() if line.strip()]


def publish_events(
    settings: Settings,
    events: list[dict],
    interval_seconds: float,
) -> int:
    """Publica eventos no tópico configurado. Requer broker acessível."""
    from confluent_kafka import Producer  # import tardio: só quando publicar

    logger = configure_logger(name="stream_producer", level=settings.log_level)
    producer = Producer({"bootstrap.servers": settings.kafka_bootstrap_servers})
    published = 0

    def _delivery(err, msg) -> None:
        if err is not None:
            logger.error("Falha ao entregar evento: %s", err)
        else:
            logger.debug("Evento entregue em %s[%s]", msg.topic(), msg.partition())

    for event in events:
        if event["sigla_uf"] not in UFS_VALIDAS:
            event["codigo_municipio"] = SIGLA_TO_CODIGO_UF.get(
                event["sigla_uf"], event["codigo_municipio"]
            )
        producer.produce(
            settings.kafka_topic,
            key=event["event_id"],
            value=json.dumps(event).encode("utf-8"),
            callback=_delivery,
        )
        producer.poll(0)
        published += 1
        logger.info("Publicado evento %s (%s)", published, event["event_id"])
        if interval_seconds > 0:
            time.sleep(interval_seconds)

    producer.flush()
    logger.info("Publicação concluída: %s evento(s).", published)
    return published


def run_producer(
    settings: Settings,
    events: int,
    interval: float,
    source_file: Path | None = None,
) -> int:
    """Ponto de entrada do produtor (usado pela CLI)."""
    payload = (
        load_events_file(source_file) if source_file else generate_events(events)
    )
    return publish_events(settings, payload, interval)

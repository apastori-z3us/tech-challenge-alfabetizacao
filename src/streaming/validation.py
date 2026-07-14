"""Validação de eventos de streaming (independente de Kafka)."""

from __future__ import annotations

import json
import re
from datetime import datetime
from functools import lru_cache
from pathlib import Path

from src.quality.reference import UFS_VALIDAS

SCHEMA_PATH = Path(__file__).resolve().parent / "schemas" / "event.schema.json"

_CODIGO_MUNICIPIO_RE = re.compile(r"^\d{7}$")
_SIGLA_UF_RE = re.compile(r"^[A-Z]{2}$")


@lru_cache(maxsize=1)
def load_schema() -> dict:
    """Carrega o JSON Schema do evento."""
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def validate_event(event: dict) -> tuple[bool, list[str]]:
    """Valida um evento contra o contrato. Retorna (válido, lista_de_erros)."""
    errors: list[str] = []
    schema = load_schema()

    for field in schema["required"]:
        if event.get(field) in (None, ""):
            errors.append(f"campo obrigatório ausente: {field}")
    if errors:
        return False, errors

    codigo = str(event["codigo_municipio"])
    if not _CODIGO_MUNICIPIO_RE.match(codigo):
        errors.append("codigo_municipio deve ter 7 dígitos")

    sigla = str(event["sigla_uf"]).upper()
    if not _SIGLA_UF_RE.match(sigla) or sigla not in UFS_VALIDAS:
        errors.append(f"sigla_uf inválida: {event['sigla_uf']}")

    try:
        taxa = float(event["taxa_alfabetizacao"])
        if not 0.0 <= taxa <= 100.0:
            errors.append("taxa_alfabetizacao fora do intervalo [0, 100]")
    except (TypeError, ValueError):
        errors.append("taxa_alfabetizacao não numérica")

    try:
        ano = int(event["ano_referencia"])
        if not 1990 <= ano <= 2100:
            errors.append("ano_referencia fora do intervalo plausível")
    except (TypeError, ValueError):
        errors.append("ano_referencia não inteiro")

    try:
        _parse_iso(str(event["event_time"]))
    except ValueError:
        errors.append("event_time não está em ISO-8601")

    return (len(errors) == 0), errors


def _parse_iso(value: str) -> datetime:
    """Converte um timestamp ISO-8601 (aceita sufixo 'Z')."""
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def event_latency_seconds(event_time: str, ingestion_time: str) -> float:
    """Latência (s) entre a geração do evento e a ingestão."""
    delta = _parse_iso(ingestion_time) - _parse_iso(event_time)
    return round(delta.total_seconds(), 3)

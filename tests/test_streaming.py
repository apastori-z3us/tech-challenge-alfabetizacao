"""Testes do fluxo de streaming (independentes de Kafka)."""

from __future__ import annotations

from src.common.io_utils import read_parquet_dir
from src.streaming.consumer import ConsumerStats, process_event
from src.streaming.deduplication import Deduplicator
from src.streaming.microbatch import MicroBatcher
from src.streaming.producer import generate_event, generate_events
from src.streaming.validation import validate_event


def _valid_event() -> dict:
    return {
        "event_id": "evt-1",
        "event_type": "indicador_atualizado",
        "codigo_municipio": "3550308",
        "sigla_uf": "SP",
        "ano_referencia": 2026,
        "taxa_alfabetizacao": 88.5,
        "event_time": "2026-07-13T10:00:00+00:00",
        "source": "simulador",
        "schema_version": "1.0",
    }


def test_valid_event_passes():
    ok, errors = validate_event(_valid_event())
    assert ok and errors == []


def test_generated_events_are_valid():
    assert len(generate_events(5)) == 5
    ok, errors = validate_event(generate_event())
    assert ok, errors


def test_invalid_taxa_rejected():
    event = _valid_event()
    event["taxa_alfabetizacao"] = 150.0
    ok, errors = validate_event(event)
    assert not ok
    assert any("taxa" in e for e in errors)


def test_missing_municipio_rejected():
    event = _valid_event()
    event["codigo_municipio"] = ""
    ok, errors = validate_event(event)
    assert not ok


def test_invalid_uf_rejected():
    event = _valid_event()
    event["sigla_uf"] = "ZZ"
    ok, errors = validate_event(event)
    assert not ok


def test_deduplication():
    dedup = Deduplicator()
    events = [_valid_event(), _valid_event()]  # mesmo event_id
    new, dups = dedup.filter_new(events)
    assert len(new) == 1
    assert dups == 1


def test_process_event_valid_and_microbatch(settings):
    dedup = Deduplicator()
    batcher = MicroBatcher(settings, batch_size=1)
    stats = ConsumerStats()
    result = process_event(settings, _valid_event(), dedup, batcher, stats)
    assert result == "valid"
    assert batcher.pending() == 1
    path = batcher.flush()
    assert path is not None
    df = read_parquet_dir(settings.bronze_path / "streaming")
    assert len(df) == 1
    assert df.iloc[0]["_load_type"] == "STREAMING"


def test_process_event_invalid_quarantine(settings):
    dedup = Deduplicator()
    batcher = MicroBatcher(settings)
    stats = ConsumerStats()
    bad = _valid_event()
    bad["taxa_alfabetizacao"] = 999
    result = process_event(settings, bad, dedup, batcher, stats)
    assert result == "invalid"
    quarantine = settings.quarantine_path / "streaming"
    assert list(quarantine.rglob("*.json"))


def test_process_event_duplicate(settings):
    dedup = Deduplicator()
    batcher = MicroBatcher(settings)
    stats = ConsumerStats()
    process_event(settings, _valid_event(), dedup, batcher, stats)
    result = process_event(settings, _valid_event(), dedup, batcher, stats)
    assert result == "duplicate"
    assert stats.duplicates == 1

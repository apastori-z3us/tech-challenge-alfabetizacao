"""Deduplicação de eventos de streaming por `event_id`.

Suporta reprocessamento: os `event_id` já persistidos podem semear o deduplicador
para que uma nova execução não gere duplicatas na Bronze de streaming.
"""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

import pandas as pd


class Deduplicator:
    """Rastreia `event_id` já vistos (em memória)."""

    def __init__(self, seen: Iterable[str] | None = None) -> None:
        self._seen: set[str] = set(seen or [])

    def is_duplicate(self, event_id: str) -> bool:
        return event_id in self._seen

    def add(self, event_id: str) -> None:
        self._seen.add(event_id)

    def seen_count(self) -> int:
        return len(self._seen)

    def filter_new(self, events: list[dict]) -> tuple[list[dict], int]:
        """Separa eventos novos, contabilizando duplicatas."""
        new_events: list[dict] = []
        duplicates = 0
        for event in events:
            event_id = str(event.get("event_id", ""))
            if not event_id or self.is_duplicate(event_id):
                duplicates += 1
                continue
            self.add(event_id)
            new_events.append(event)
        return new_events, duplicates

    @classmethod
    def from_bronze(cls, bronze_dir: Path) -> Deduplicator:
        """Semeia o deduplicador a partir dos event_id já persistidos."""
        seen: set[str] = set()
        if bronze_dir.exists():
            for parquet in bronze_dir.rglob("*.parquet"):
                frame = pd.read_parquet(parquet, columns=None)
                if "event_id" in frame.columns:
                    seen.update(frame["event_id"].astype(str).tolist())
        return cls(seen)

"""Microbatch de streaming: acumula eventos e materializa Parquet na Bronze.

Aciona por quantidade de eventos ou por intervalo de tempo. A transformação
JSON → Parquet permite carregar lotes na Bronze BigQuery (nunca streaming direto
do BigQuery) e, na sequência, aplicar Silver.
"""

from __future__ import annotations

import time
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import pandas as pd

from src.common.io_utils import partition_dir, write_parquet
from src.common.settings import Settings


def events_to_dataframe(events: list[dict], ingestion_time: str) -> pd.DataFrame:
    """Converte eventos validados em DataFrame com metadados de ingestão."""
    frame = pd.DataFrame(events)
    frame["_ingestion_time"] = ingestion_time
    frame["_load_type"] = "STREAMING"
    return frame


class MicroBatcher:
    """Acumula eventos e materializa lotes na Bronze de streaming."""

    def __init__(
        self,
        settings: Settings,
        batch_size: int | None = None,
        interval_seconds: int | None = None,
    ) -> None:
        self.settings = settings
        self.batch_size = batch_size or settings.streaming_batch_size
        self.interval_seconds = (
            interval_seconds or settings.streaming_batch_interval_seconds
        )
        self._buffer: list[dict] = []
        self._last_flush = time.monotonic()

    def add(self, event: dict) -> None:
        self._buffer.append(event)

    def pending(self) -> int:
        return len(self._buffer)

    def should_flush(self) -> bool:
        if not self._buffer:
            return False
        by_size = len(self._buffer) >= self.batch_size
        by_time = (time.monotonic() - self._last_flush) >= self.interval_seconds
        return by_size or by_time

    def flush(self) -> Path | None:
        """Grava o lote acumulado em Parquet e limpa o buffer."""
        if not self._buffer:
            return None
        ingestion_time = datetime.now(timezone.utc).isoformat()
        frame = events_to_dataframe(self._buffer, ingestion_time)
        ingestion_date = ingestion_time[:10]
        directory = partition_dir(
            self.settings.bronze_path / "streaming",
            "indicador",
            "ingestion_date",
            ingestion_date,
        )
        path = directory / f"microbatch_{uuid4()}.parquet"
        write_parquet(frame, path)
        self._buffer = []
        self._last_flush = time.monotonic()
        return path

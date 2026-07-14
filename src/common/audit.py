"""Auditoria e observabilidade estruturada.

Escreve registros de auditoria em:
- arquivos JSON por execução (relatórios de qualidade);
- arquivos JSON Lines locais (pipeline_runs, quality_results, streaming_metrics);
- tabelas BigQuery de auditoria (opcional, quando um cliente é fornecido).

A escrita no BigQuery é injetável e silenciosamente ignorada offline, de modo que
a observabilidade local nunca depende de credenciais.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from src.common.io_utils import append_jsonl, write_json
from src.common.logger import configure_logger
from src.common.settings import Settings

logger = configure_logger(name="audit")


@dataclass
class PipelineRun:
    """Registro de auditoria de uma execução de pipeline."""

    pipeline_name: str
    source: str
    layer: str
    status: str
    records_read: int = 0
    records_written: int = 0
    records_valid: int = 0
    records_rejected: int = 0
    bytes_processed: int = 0
    error_type: str | None = None
    error_message: str | None = None
    pipeline_run_id: str = field(default_factory=lambda: str(uuid4()))
    start_time: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    end_time: str | None = None
    duration_seconds: float | None = None


def write_quality_report(settings: Settings, report_dict: dict) -> Path:
    """Grava o relatório JSON de qualidade em data/audit/quality/<entity>/."""
    entity = report_dict.get("entity", "desconhecida")
    run_id = report_dict.get("quality_run_id", str(uuid4()))
    path = settings.audit_path / "quality" / entity / f"{run_id}.json"
    write_json(report_dict, path)
    return path


def record_quality_result(settings: Settings, report_dict: dict) -> Path:
    """Anexa o resultado de qualidade ao JSONL `quality_results`."""
    path = settings.audit_path / "quality_results.jsonl"
    return append_jsonl(report_dict, path)


def record_pipeline_run(settings: Settings, run: PipelineRun) -> Path:
    """Finaliza e anexa um registro de pipeline_run ao JSONL local."""
    if run.end_time is None:
        run.end_time = datetime.now(timezone.utc).isoformat()
    if run.duration_seconds is None:
        start = datetime.fromisoformat(run.start_time)
        end = datetime.fromisoformat(run.end_time)
        run.duration_seconds = round((end - start).total_seconds(), 3)
    path = settings.audit_path / "pipeline_runs.jsonl"
    append_jsonl(asdict(run), path)
    logger.info(
        "pipeline_run registrado: %s | status=%s | lidos=%s | escritos=%s",
        run.pipeline_name,
        run.status,
        run.records_read,
        run.records_written,
    )
    return path


def record_streaming_metric(settings: Settings, metric: dict) -> Path:
    """Anexa uma métrica de streaming ao JSONL local."""
    path = settings.audit_path / "streaming_metrics.jsonl"
    return append_jsonl(metric, path)

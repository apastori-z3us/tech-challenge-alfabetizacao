"""Gera um relatório de monitoramento a partir dos logs de auditoria (JSONL).

Observabilidade sem serviços pagos: consolida `pipeline_runs`, `quality_results`
e `streaming_metrics` locais em um resumo legível.
"""

from __future__ import annotations

import json
from pathlib import Path

from src.common.settings import Settings, load_settings


def _read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    records = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            records.append(json.loads(line))
    return records


def build_report(settings: Settings | None = None) -> dict:
    settings = settings or load_settings()
    runs = _read_jsonl(settings.audit_path / "pipeline_runs.jsonl")
    quality = _read_jsonl(settings.audit_path / "quality_results.jsonl")
    streaming = _read_jsonl(settings.audit_path / "streaming_metrics.jsonl")

    last_run = runs[-1] if runs else None
    total_valid = sum(q.get("valid_count", 0) for q in quality)
    total_invalid = sum(q.get("invalid_count", 0) for q in quality)
    entities = sorted({q.get("entity") for q in quality if q.get("entity")})
    last_stream = streaming[-1] if streaming else None

    return {
        "total_pipeline_runs": len(runs),
        "ultima_execucao": last_run,
        "entidades_processadas": entities,
        "registros_validos": total_valid,
        "registros_rejeitados": total_invalid,
        "taxa_rejeicao_pct": round(
            100.0 * total_invalid / (total_valid + total_invalid), 2
        )
        if (total_valid + total_invalid)
        else 0.0,
        "streaming": {
            "sessoes": len(streaming),
            "ultima": last_stream,
            "latencia_media_s": last_stream.get("avg_latency_seconds")
            if last_stream
            else None,
            "duplicados": last_stream.get("duplicates") if last_stream else None,
        },
    }


def main() -> int:
    report = build_report()
    print(json.dumps(report, ensure_ascii=False, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

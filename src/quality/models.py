"""Modelos de dados do framework de qualidade."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

import pandas as pd


class Severity(str, Enum):
    """Severidade de uma regra de qualidade."""

    CRITICAL = "CRITICAL"  # falha de schema: interrompe a transformação
    ERROR = "ERROR"  # registro inválido: vai para a quarentena


class CriticalSchemaError(RuntimeError):
    """Erro crítico de schema que impede a transformação da entidade."""


@dataclass
class RuleResult:
    """Resultado da avaliação de uma única regra."""

    rule: str
    column: str | None
    severity: Severity
    failed_count: int
    message: str

    def to_dict(self) -> dict:
        return {
            "rule": self.rule,
            "column": self.column,
            "severity": self.severity.value,
            "failed_count": self.failed_count,
            "message": self.message,
        }


@dataclass
class QualityReport:
    """Relatório completo de uma execução de qualidade."""

    entity: str
    layer: str
    quality_run_id: str
    started_at: datetime
    finished_at: datetime
    total_read: int
    valid_count: int
    invalid_count: int
    rule_results: list[RuleResult] = field(default_factory=list)
    valid_df: pd.DataFrame = field(default_factory=pd.DataFrame)
    invalid_df: pd.DataFrame = field(default_factory=pd.DataFrame)
    silver_path: str | None = None
    quarantine_path: str | None = None
    error_message: str | None = None

    @property
    def status(self) -> str:
        if self.error_message:
            return "FAILED"
        if self.invalid_count > 0:
            return "PASSED_WITH_WARNINGS"
        return "PASSED"

    @property
    def duration_seconds(self) -> float:
        return round((self.finished_at - self.started_at).total_seconds(), 3)

    @property
    def failures_by_rule(self) -> dict[str, int]:
        return {
            r.rule: r.failed_count for r in self.rule_results if r.failed_count > 0
        }

    def to_dict(self) -> dict:
        """Serializa o relatório (sem os DataFrames) para JSON/auditoria."""
        return {
            "quality_run_id": self.quality_run_id,
            "pipeline": f"quality_{self.entity}",
            "entity": self.entity,
            "layer": self.layer,
            "status": self.status,
            "started_at": self.started_at.isoformat(),
            "finished_at": self.finished_at.isoformat(),
            "duration_seconds": self.duration_seconds,
            "total_read": self.total_read,
            "valid_count": self.valid_count,
            "invalid_count": self.invalid_count,
            "failures_by_rule": self.failures_by_rule,
            "rule_results": [r.to_dict() for r in self.rule_results],
            "silver_path": self.silver_path,
            "quarantine_path": self.quarantine_path,
            "error_message": self.error_message,
        }

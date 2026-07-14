"""Framework reutilizável de qualidade de dados.

Fornece verificações primitivas (máscaras booleanas por linha), padronizações e
um motor genérico (`run_quality`) dirigido por uma especificação declarativa
(`EntityQualitySpec`). O mesmo motor atende municípios, UF, metas e indicadores.
"""

from __future__ import annotations

import re
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4

import pandas as pd

from src.quality.models import (
    CriticalSchemaError,
    QualityReport,
    RuleResult,
    Severity,
)

# --------------------------------------------------------------------------- #
# Verificações primitivas — retornam máscara booleana (True = registro VÁLIDO) #
# --------------------------------------------------------------------------- #


def not_null(series: pd.Series) -> pd.Series:
    """True onde o valor não é nulo nem string vazia/espaços."""
    stripped = series.astype("string").str.strip()
    return series.notna() & stripped.ne("") & stripped.notna()


def matches_regex(series: pd.Series, pattern: str) -> pd.Series:
    """True onde o valor casa integralmente com o padrão."""
    compiled = re.compile(pattern)
    return series.astype("string").str.fullmatch(compiled).fillna(False)


def in_set(series: pd.Series, allowed: Sequence[str]) -> pd.Series:
    """True onde o valor pertence ao conjunto permitido."""
    allowed_set = set(allowed)
    return series.astype("string").isin(allowed_set).fillna(False)


def numeric_between(
    series: pd.Series, minimum: float, maximum: float
) -> pd.Series:
    """True onde o valor numérico está no intervalo fechado [min, max]."""
    numeric = pd.to_numeric(series, errors="coerce")
    return numeric.between(minimum, maximum).fillna(False)


def is_numeric(series: pd.Series) -> pd.Series:
    """True onde o valor pode ser interpretado como número."""
    return pd.to_numeric(series, errors="coerce").notna()


# --------------------------------------------------------------------------- #
# Padronizações                                                               #
# --------------------------------------------------------------------------- #


def strip_text(series: pd.Series) -> pd.Series:
    """Remove espaços excedentes (bordas e internos duplicados)."""
    as_str = series.astype("string")
    collapsed = as_str.str.strip().str.replace(r"\s+", " ", regex=True)
    return collapsed


def upper_text(series: pd.Series) -> pd.Series:
    return strip_text(series).str.upper()


def hash_text(series: pd.Series) -> pd.Series:
    """Anonimiza um identificador via SHA-256 (irreversível)."""
    import hashlib

    return series.astype("string").fillna("").map(
        lambda value: hashlib.sha256(value.encode("utf-8")).hexdigest()
    )


def year_valid(series: pd.Series, minimum: int = 1990, maximum: int = 2100):
    """True onde o valor é um ano plausível (numérico dentro do intervalo)."""
    return numeric_between(series, minimum, maximum)


# --------------------------------------------------------------------------- #
# Especificação declarativa de qualidade por entidade                         #
# --------------------------------------------------------------------------- #

RuleFn = Callable[[pd.DataFrame], pd.Series]


@dataclass
class ColumnRule:
    """Regra de qualidade em nível de linha.

    `func` recebe o DataFrame e devolve uma máscara booleana onde True indica
    registro VÁLIDO para aquela regra.
    """

    name: str
    func: RuleFn
    column: str | None = None
    severity: Severity = Severity.ERROR


@dataclass
class EntityQualitySpec:
    """Especificação declarativa de qualidade de uma entidade."""

    entity: str
    required_columns: Sequence[str]
    rules: Sequence[ColumnRule] = field(default_factory=list)
    unique_keys: Sequence[str] = field(default_factory=list)
    standardizers: dict[str, Callable[[pd.Series], pd.Series]] = field(
        default_factory=dict
    )


def _apply_standardizers(
    dataframe: pd.DataFrame, spec: EntityQualitySpec
) -> pd.DataFrame:
    result = dataframe.copy()
    for column, func in spec.standardizers.items():
        if column in result.columns:
            result[column] = func(result[column])
    return result


def run_quality(
    dataframe: pd.DataFrame,
    spec: EntityQualitySpec,
    *,
    layer: str = "silver",
) -> QualityReport:
    """Executa todas as regras da especificação e separa válidos/inválidos.

    Levanta `CriticalSchemaError` quando faltam colunas obrigatórias.
    """
    started_at = datetime.now(timezone.utc)
    quality_run_id = str(uuid4())
    total_read = len(dataframe)

    # 1. Verificação crítica de schema.
    missing = [c for c in spec.required_columns if c not in dataframe.columns]
    if missing:
        finished_at = datetime.now(timezone.utc)
        report = QualityReport(
            entity=spec.entity,
            layer=layer,
            quality_run_id=quality_run_id,
            started_at=started_at,
            finished_at=finished_at,
            total_read=total_read,
            valid_count=0,
            invalid_count=total_read,
            rule_results=[
                RuleResult(
                    rule="schema.required_columns",
                    column=None,
                    severity=Severity.CRITICAL,
                    failed_count=total_read,
                    message=f"Colunas obrigatórias ausentes: {sorted(missing)}",
                )
            ],
            error_message=f"Colunas obrigatórias ausentes: {sorted(missing)}",
        )
        raise CriticalSchemaError(report.error_message)

    # 2. Padronização.
    standardized = _apply_standardizers(dataframe, spec)

    # 3. Avaliação das regras de linha.
    valid_mask = pd.Series(True, index=standardized.index)
    rule_results: list[RuleResult] = []

    for rule in spec.rules:
        mask = rule.func(standardized).reindex(standardized.index).fillna(False)
        failed = int((~mask).sum())
        rule_results.append(
            RuleResult(
                rule=rule.name,
                column=rule.column,
                severity=rule.severity,
                failed_count=failed,
                message=f"{failed} registro(s) reprovado(s) na regra {rule.name}.",
            )
        )
        valid_mask &= mask

    # 4. Unicidade das chaves lógicas.
    if spec.unique_keys and total_read > 0:
        present_keys = [k for k in spec.unique_keys if k in standardized.columns]
        if present_keys:
            dup_mask = standardized.duplicated(subset=present_keys, keep="first")
            failed = int(dup_mask.sum())
            rule_results.append(
                RuleResult(
                    rule=f"unique.{'_'.join(present_keys)}",
                    column=",".join(present_keys),
                    severity=Severity.ERROR,
                    failed_count=failed,
                    message=f"{failed} registro(s) duplicado(s) em {present_keys}.",
                )
            )
            valid_mask &= ~dup_mask

    valid_df = standardized[valid_mask].reset_index(drop=True)
    invalid_df = standardized[~valid_mask].reset_index(drop=True)

    finished_at = datetime.now(timezone.utc)
    return QualityReport(
        entity=spec.entity,
        layer=layer,
        quality_run_id=quality_run_id,
        started_at=started_at,
        finished_at=finished_at,
        total_read=total_read,
        valid_count=len(valid_df),
        invalid_count=len(invalid_df),
        rule_results=rule_results,
        valid_df=valid_df,
        invalid_df=invalid_df,
    )

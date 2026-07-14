"""Modelos de configuração das fontes Batch."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ColumnContract:
    """Contrato de uma coluna esperada de uma fonte."""

    name: str
    type: str
    nullable: bool = True


@dataclass(frozen=True)
class SourceConfig:
    """Configuração declarativa de uma fonte de ingestão."""

    name: str
    description: str
    table_id: str
    enabled: bool
    ingestion_type: str
    schema_version: str
    layer_targets: tuple[str, ...]
    key_columns: tuple[str, ...]
    selected_columns: tuple[str, ...]
    partition_columns: tuple[str, ...] = field(default_factory=tuple)
    expected_schema: tuple[ColumnContract, ...] = field(default_factory=tuple)

    @property
    def is_bigquery_source(self) -> bool:
        """True se a fonte aponta para uma tabela BigQuery real."""
        return (
            self.ingestion_type == "batch"
            and self.table_id
            and not self.table_id.startswith(("PREENCHER", "DERIVED"))
        )

    @property
    def source_project(self) -> str:
        return self.table_id.split(".")[0] if "." in self.table_id else ""

    @property
    def source_dataset(self) -> str:
        parts = self.table_id.split(".")
        return parts[1] if len(parts) >= 3 else ""

    @property
    def source_table(self) -> str:
        parts = self.table_id.split(".")
        return parts[-1] if parts else ""

    def validate(self) -> None:
        """Valida a coerência mínima da configuração."""
        if not self.name:
            raise ValueError("Fonte sem nome.")
        if not self.selected_columns:
            raise ValueError(f"Fonte '{self.name}' sem selected_columns.")
        for key in self.key_columns:
            if key not in self.selected_columns:
                raise ValueError(
                    f"Fonte '{self.name}': key_column '{key}' não está em "
                    "selected_columns."
                )


def parse_source(name: str, payload: dict) -> SourceConfig:
    """Constrói um `SourceConfig` a partir do dicionário do YAML."""
    schema = payload.get("expected_schema", {}) or {}
    contracts = tuple(
        ColumnContract(
            name=col,
            type=str(spec.get("type", "STRING")),
            nullable=bool(spec.get("nullable", True)),
        )
        for col, spec in schema.items()
    )
    return SourceConfig(
        name=name,
        description=str(payload.get("description", "")),
        table_id=str(payload.get("table_id", "")),
        enabled=bool(payload.get("enabled", False)),
        ingestion_type=str(payload.get("ingestion_type", "batch")),
        schema_version=str(payload.get("schema_version", "1.0")),
        layer_targets=tuple(payload.get("layer_targets", []) or []),
        key_columns=tuple(payload.get("key_columns", []) or []),
        selected_columns=tuple(payload.get("selected_columns", []) or []),
        partition_columns=tuple(payload.get("partition_columns", []) or []),
        expected_schema=contracts,
    )

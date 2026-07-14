"""Testes de contrato entre sources.yaml e as regras de qualidade."""

from __future__ import annotations

import pytest

from src.batch.registry import load_sources
from src.quality.rules import SPEC_BUILDERS

pytestmark = pytest.mark.contracts


def test_key_columns_subset_of_selected(settings):
    for name, source in load_sources(settings).items():
        for key in source.key_columns:
            assert key in source.selected_columns, f"{name}: {key} fora de selected"


def test_expected_schema_matches_selected(settings):
    for name, source in load_sources(settings).items():
        schema_cols = {c.name for c in source.expected_schema}
        assert schema_cols.issubset(set(source.selected_columns)), name


def test_quality_spec_columns_available(settings):
    """As colunas obrigatórias da spec devem existir no contrato da fonte."""
    sources = load_sources(settings)
    for entity, builder in SPEC_BUILDERS.items():
        if entity not in sources:
            continue
        spec = builder()
        selected = set(sources[entity].selected_columns)
        missing = [c for c in spec.required_columns if c not in selected]
        assert not missing, f"{entity}: obrigatórias fora do contrato: {missing}"

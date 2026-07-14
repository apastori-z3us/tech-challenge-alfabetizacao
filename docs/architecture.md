# Arquitetura

Arquitetura Medalhão híbrida (Batch + Streaming). Visão geral no
[README](../README.md#8-diagrama); detalhes por tema nos documentos abaixo.

## Camadas

- **Bronze** — dados brutos + metadados de ingestão (Parquet particionado + BQ).
- **Silver** — dados limpos, padronizados e validados (qualidade + quarentena).
- **Gold** — produtos analíticos agregados.

## Componentes

| Componente | Módulo |
| --- | --- |
| Ingestão Batch configurável | `src/batch/` |
| Carga Bronze | `src/bronze/loader.py` |
| Qualidade | `src/quality/` |
| Silver | `src/silver/` |
| Integração + Gold | `src/gold/` |
| Streaming | `src/streaming/` |
| Orquestração (CLI) | `src/cli.py` |
| Configuração/observabilidade | `src/common/` |

## Documentos relacionados

- Fontes: [source_inventory.md](source_inventory.md),
  [data_dictionary.md](data_dictionary.md), [data_contracts.md](data_contracts.md)
- Qualidade: [quality_rules.md](quality_rules.md)
- Integração: [relationship_matrix.md](relationship_matrix.md)
- Linhagem: [data_lineage.md](data_lineage.md)
- FinOps/Segurança: [finops.md](finops.md),
  [security_and_governance.md](security_and_governance.md)
- Monitoramento: [monitoring.md](monitoring.md)
- Bloqueios: [blockers.md](blockers.md)

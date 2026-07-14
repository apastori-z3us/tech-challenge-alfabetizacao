# Evidência de Execução — Batch → Bronze

- **Data:** 2026-07-14
- **Projeto:** rising-reserve-352718 (BigQuery Sandbox)
- **Comando:** `python -m src.cli batch` (e por fonte)
- **Fontes reais:** `basedosdados.br_bd_diretorios_brasil` (municipio, uf) e
  `basedosdados.br_inep_avaliacao_alfabetizacao` (metas, indicador, alunos).

Validação por fonte: `registros_extraidos = registros_parquet = registros_bigquery`.

| Fonte | Registros | Parquet | BigQuery (`tc_alfabetizacao_bronze`) | Status |
| --- | ---: | :---: | ---: | :---: |
| municipio | 5.571 | ✅ | 5.571 | ✅ |
| uf | 27 | ✅ | 27 | ✅ |
| meta_brasil | 3 | ✅ | 3 | ✅ |
| meta_uf | 79 | ✅ | 79 | ✅ |
| meta_municipio | 10.704 | ✅ | 10.704 | ✅ |
| indicador_alfabetizacao | 10.896 | ✅ | 10.896 | ✅ |
| aluno | 100.000 | ✅ | 100.000 | ✅ |

## Bytes processados (FinOps)

As consultas usam `dry run` + `maximum_bytes_billed` (1 GB) e **cache de
consulta**. Nas execuções repetidas o cache resultou em **0 bytes faturados**
(`bytes_processed = 0` na auditoria), o que é o comportamento desejado de FinOps.
As estimativas de bytes são registradas nos logs de `dry run` de cada fonte.

## Metadados e idempotência

Cada registro Bronze recebe: `_ingestion_id`, `_ingestion_timestamp`,
`_source_project`, `_source_dataset`, `_source_table`, `_load_type`,
`_record_hash`, `_schema_version`. A Bronze BigQuery é snapshot idempotente
(`WRITE_TRUNCATE`); o histórico é preservado em Parquet particionado por
`ingestion_date=`. A camada seguinte consome o último snapshot
(`read_latest_parquet`), evitando duplicação em reexecuções.

## Nenhuma tabela vazia / nenhuma divergência

Todas as fontes retornaram registros e as contagens Parquet e BigQuery
coincidiram (invariante verificado no `run_batch_source`).

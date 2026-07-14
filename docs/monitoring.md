# Monitoramento e Observabilidade

Como o projeto **não utiliza serviços pagos** de monitoramento, a observabilidade
é implementada por **logs estruturados**, **arquivos de auditoria (JSON Lines)** e
**tabelas de auditoria no BigQuery** (quando a execução chega à nuvem).

## Três destinos de log

1. **Terminal** — `src/common/logger.py` (formato padronizado com timestamp/nível).
2. **Arquivos JSON Lines locais** — `src/common/audit.py`:
   - `data/audit/pipeline_runs.jsonl`
   - `data/audit/quality_results.jsonl`
   - `data/audit/streaming_metrics.jsonl`
   - `data/audit/quality/<entidade>/<quality_run_id>.json`
3. **Tabelas de auditoria BigQuery** (quando acessível):
   - `tc_alfabetizacao_audit.pipeline_runs`
   - `tc_alfabetizacao_audit.quality_results`
   - `tc_alfabetizacao_audit.streaming_metrics`

## Campos de cada execução (`pipeline_runs`)

`pipeline_run_id`, `pipeline_name`, `source`, `layer`, `start_time`, `end_time`,
`duration_seconds`, `status`, `records_read`, `records_written`, `records_valid`,
`records_rejected`, `bytes_processed`, `error_type`, `error_message`.

## Relatório de monitoramento

`scripts/generate_monitoring_report.py` consolida os JSONL e imprime:

- última execução e duração;
- volume (válidos/rejeitados) e taxa de rejeição;
- entidades processadas;
- status das camadas;
- latência média do streaming e eventos duplicados.

```powershell
python scripts/generate_monitoring_report.py
```

## Métricas de streaming

O consumidor registra por sessão: consumidos, válidos, inválidos, duplicados,
lotes materializados (`flushed_batches`) e latência média (`event_time` →
`ingestion_time`).

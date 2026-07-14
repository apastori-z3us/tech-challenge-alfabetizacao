# Evidência de Execução — Streaming ao Vivo (Redpanda)

- **Data:** 2026-07-14
- **Infra:** `docker compose up -d redpanda` (Redpanda v24.2.7, healthy, porta 19092)
- **Comandos:**
  - `python -m src.cli stream-producer --events 20 --interval 0`
  - `python -m src.cli stream-consumer --max-events 20`
  - `python -m src.cli stream-producer --file <edge_events.jsonl>`
  - `python -m src.cli stream-consumer --max-events 6`
  - `docker compose down`

## Sessão 1 — fluxo válido

| Métrica | Valor |
| --- | ---: |
| Publicados | 20 |
| Consumidos | 20 |
| Válidos | 20 |
| Inválidos | 0 |
| Duplicados | 0 |
| Microbatches gerados | 1 |
| Latência média (s) | 10.272 |

## Sessão 2 — casos de borda

Arquivo controlado: 2 válidos, 1 duplicado, 1 taxa fora de 0–100, 1 sem
município, 1 UF inválida.

| Métrica | Valor |
| --- | ---: |
| Consumidos | 6 |
| Válidos | 2 |
| Inválidos | 3 |
| Duplicados | 1 |
| Microbatches gerados | 1 |
| Latência média (s) | 27.935 |

Quarentena gerada (`data/quarantine/streaming/indicador/ingestion_date=2026-07-14/`):

- `edge-badtaxa.json` (taxa 150 fora do intervalo)
- `edge-baduf.json` (UF "ZZ" inválida)
- `edge-nomuni.json` (município ausente)
- `edge-valid-1.json` (evento duplicado)

## Validações confirmadas ao vivo

- ✅ Schema validado (JSON Schema do evento)
- ✅ `event_id` único e **deduplicação** (duplicado não reprocessado)
- ✅ Evento inválido → **quarentena**; válido → **Bronze streaming**
- ✅ **Microbatch** materializado em Parquet (2 arquivos, 22 eventos válidos)
- ✅ `event_time`/`ingestion_time` e **latência** calculados
- ✅ **Métricas** gravadas em `data/audit/streaming_metrics.jsonl`
- ✅ Confirmação de mensagem após persistência; broker encerrado com
  `docker compose down`

## Arquivos gerados

```text
data/bronze/streaming/indicador/ingestion_date=2026-07-14/microbatch_*.parquet  (2)
data/quarantine/streaming/indicador/ingestion_date=2026-07-14/*.json            (4)
data/audit/streaming_metrics.jsonl                                              (2 sessões)
```

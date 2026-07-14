# FinOps — Controle e Otimização de Custos

O projeto é **custo-zero**: usa **BigQuery Sandbox** (sem faturamento) e execução
local com Parquet. Esta seção descreve e demonstra as práticas de otimização.

## Ausência de faturamento

- **BigQuery Sandbox**: sem cartão de crédito e sem billing habilitado.
- **Sem serviços pagos**: nada de Cloud Storage, Pub/Sub, Cloud Run ou Dataflow.
- Streaming simulado localmente com **Redpanda em Docker** (gratuito).

## Controles aplicados no código

| Prática | Onde | Efeito |
| --- | --- | --- |
| `maximum_bytes_billed` (1 GB/consulta) | `src/batch/extractor.py` | Aborta consultas caras |
| **Dry run** antes de consultar | `BigQueryReader.fetch` | Estima bytes; barra excessos |
| **Seleção explícita de colunas** (sem `SELECT *`) | `src/batch/queries.py`, `sources.yaml` | Menos bytes lidos |
| **LIMIT na descoberta** | `docs/source_inventory.md` | Amostragem barata |
| **Parquet + Snappy** | `src/common/io_utils.py` | Armazenamento comprimido |
| **Cache de consulta** (`use_query_cache=True`) | `BigQueryReader` | Reuso sem custo |
| **Idempotência / anti-reprocessamento** | hash de registro, dedup por `event_id` | Evita cargas repetidas |
| **Snapshot Bronze (`WRITE_TRUNCATE`)** | `src/bronze/loader.py` | Sandbox enxuto; histórico em Parquet |
| **Tabelas Gold agregadas** | `src/gold/build.py` | Consultas analíticas baratas |
| **Consultas filtradas / particionamento local** | `ingestion_date=`, `processing_date=` | Leitura seletiva |

## Retenção e arquivos pequenos

- Histórico preservado em Parquet particionado por data (`data/bronze/...`).
- Microbatch do streaming agrupa eventos antes de gravar, evitando muitos
  arquivos minúsculos (controle por tamanho **ou** tempo).

## Estimativa de bytes

O `dry run` informa os bytes estimados antes de qualquer cobrança; a extração só
prossegue se o valor estiver abaixo de `MAX_BYTES_BILLED`.

## Limitações de armazenamento (Sandbox)

O BigQuery Sandbox aplica expiração automática de tabelas (60 dias) e cotas de
armazenamento; por isso o **histórico canônico** vive nos Parquet locais, e o
Sandbox guarda o **snapshot atual** — decisão documentada em `docs/blockers.md`.

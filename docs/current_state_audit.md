# Auditoria do Estado Atual — Fase 0

**Data:** 2026-07-13
**Aluna:** Ana Beatriz Pastori dos Santos — RM 372884
**Branch auditada:** `main` (commit `3f9103f`)

Este relatório documenta o estado do repositório **antes** das implementações
das Fases 1 a 16, os problemas encontrados e o plano de correção.

## 1. Ambiente verificado

| Item | Resultado |
| --- | --- |
| `git branch --show-current` | `main` (após auditoria) |
| `git remote -v` | `origin` → `github.com/apastori-z3us/tech-challenge-alfabetizacao` |
| `python --version` | Python 3.12.10 |
| `python -m pip --version` | pip 26.1.2 (venv do projeto) |
| `bq ls` | ❌ Falha de autenticação (SSL/token) — ver `blockers.md` |
| `docker version` | Cliente 29.6.1 OK; **daemon não acessível** |
| `docker compose version` | v5.2.0 OK |

## 2. Arquivos existentes e responsabilidades

| Arquivo | Responsabilidade | Estado |
| --- | --- | --- |
| `src/common/settings.py` | Configuração central via `.env` | ✅ Funcional |
| `src/common/bigquery_client.py` | Fábrica de cliente BigQuery | ✅ Funcional |
| `src/common/logger.py` | Logger padrão do projeto | ✅ Funcional |
| `src/batch/extract.py` | Extração Batch de municípios → Parquet Bronze | ✅ Funcional |
| `src/bronze/loader.py` | Carga do DataFrame na Bronze BigQuery | ✅ Funcional |
| `src/main.py` | Orquestra o fluxo municípios | ✅ Funcional |
| `sql/extraction/municipio.sql` | Consulta de municípios | ✅ Funcional |
| `config/settings.yaml` | Metadados do projeto e camadas | ✅ Presente |
| `config/sources.yaml` | Catálogo de fontes | ⚠️ Fontes não-municipais com `PREENCHER_APOS_VALIDACAO` |
| `README.md` | Documentação inicial | ✅ Íntegro (sem corrupção) |
| `.gitignore` | Ignora `.env`, credenciais e dados | ✅ Correto |
| `.env.example` | Modelo de variáveis (sem segredos) | ✅ Correto |
| `requirements.txt` / `requirements-lock.txt` | Dependências | ✅ Presentes |
| `docs/*` | Documentação inicial | ⚠️ Parcial |

### Arquivos vazios (stubs) encontrados

`Dockerfile`, `compose.yaml`, `src/quality/checks.py`, `src/silver/transform.py`,
`src/gold/build.py`, `src/streaming/{producer,consumer,microbatch}.py`,
`src/streaming/schemas/event.schema.json`, `tests/test_{quality,silver,gold}.py`
e todos os `__init__.py`.

## 3. Partes concluídas

- Fluxo Batch de municípios (extração → Parquet Snappy → carga Bronze BigQuery).
- Metadados de ingestão (`_ingestion_id`, `_ingestion_timestamp`, `_source_table`,
  `_load_type`, `_record_hash`).
- Auditoria local em JSON por ingestão.
- Configuração central e logging.

## 4. Partes incompletas

- Camadas Silver e Gold (arquivos vazios).
- Framework de qualidade e quarentena.
- Streaming (Redpanda/Kafka) e `Dockerfile`/`compose.yaml`.
- Testes automatizados (todos vazios).
- CLI de orquestração, observabilidade, FinOps, governança.
- CI (GitHub Actions).
- Descoberta e validação das fontes não-municipais.

## 5. Problemas encontrados

1. **Divergência de histórico Git.** A branch `feature/municipio-silver-quality`
   havia **removido** o código funcional de Batch/Bronze (regressão). Decisão:
   não construir sobre ela; usar `main` como base e avançar `develop` (que era
   ancestral de `main`) por *fast-forward*, preservando o histórico.
2. **Lint:** 1 ocorrência `I001` (ordenação de imports) em `settings.py`.
3. **Muitos módulos vazios** referenciados pela arquitetura-alvo.
4. **Fontes não validadas** em `sources.yaml`.

## 6. Riscos

| Risco | Mitigação |
| --- | --- |
| BigQuery inacessível no ambiente | Código BQ-opcional; leitura injetável; execução offline via fixtures; blocker documentado |
| Docker daemon indisponível | `docker compose config` validado; execução do stream documentada como passo humano |
| Fabricar fontes inexistentes | Proibido; fontes ficam `enabled: false` até validação real |
| Vazamento de segredos/dados | `.gitignore` cobre `.env` e `data/`; validado |

## 7. Dependências

`requirements.txt` cobre: `google-cloud-bigquery(-storage)`, `pandas`, `pyarrow`,
`db-dtypes`, `python-dotenv`, `PyYAML`, `pydantic`, `confluent-kafka`, `tenacity`,
`pytest`, `pytest-cov`, `ruff`. Nenhuma dependência nova foi necessária para o núcleo.

## 8. Plano de correção

1. Corrigir lint e estabilizar (Fase 0).
2. Tornar a leitura de dados **injetável** para permitir execução e testes offline
   sem quebrar o fluxo BigQuery existente.
3. Implementar qualidade + Silver de municípios (Fase 1).
4. Catalogar fontes (Fase 2) sem inventar nomes.
5. Generalizar a ingestão Batch (Fase 3).
6. Silver para todas as entidades, integração e Gold (Fases 4–6).
7. Streaming, CLI, observabilidade, FinOps, testes, CI e documentação (Fases 7–16).

## 9. Arquitetura atual

```text
Base dos Dados (BigQuery público)
        -> src/batch/extract.py  -> Parquet Bronze local
                                  -> src/bronze/loader.py -> Bronze BigQuery
        -> auditoria JSON local
```

## 10. Arquitetura alvo

```text
Batch:    Fontes -> Extração configurável -> Bronze (Parquet + BQ)
                 -> Qualidade -> Silver -> Integração -> Gold
                 -> Quarentena (inválidos) -> Auditoria (JSONL + tabelas BQ)
Streaming: Produtor -> Redpanda -> Consumidor -> Bronze streaming -> microbatch -> Silver/Gold
Orquestração: src/cli.py (batch | silver | gold | quality | all | stream-*)
```

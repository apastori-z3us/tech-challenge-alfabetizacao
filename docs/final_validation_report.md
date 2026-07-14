# Relatório de Validação Final

- **Data:** 2026-07-13
- **Commit base da validação:** `565b8ea` (branch `docs/final-documentation`)
- **Ambiente:** Windows 11, PowerShell, Python 3.12.10, venv do projeto
- **Aluna:** Ana Beatriz Pastori dos Santos — RM 372884

## Comandos executados e resultados

| Comando | Resultado |
| --- | --- |
| `python -m ruff check .` | ✅ All checks passed |
| `python -m pytest -m "not integration"` | ✅ 40 passed, 2 deselected |
| `python -m pytest --cov=src` | ✅ Cobertura total **70%** (branch) |
| `python -m src.cli validate-config` | ✅ Configuração válida |
| `python -m src.cli batch --source uf` | ✅ 27 registros → Bronze Parquet |
| `python -m src.cli silver --entity uf` | ✅ 27 válidos, 0 inválidos |
| `python -m src.cli gold` | ✅ Executa; indicador BQ-gated (aviso) |
| `docker compose config --quiet` | ✅ Válido (daemon não necessário) |
| `python -m src.main` | ⚠️ Para na conexão BigQuery (bloqueio B1) |
| `bq ls ...` | ⛔ Bloqueado (auth/SSL — B1) |
| `docker compose up -d redpanda` | ⛔ Bloqueado (daemon parado — B2) |

## Testes

- 40 testes locais (unit + contracts + e2e) verdes.
- 2 testes de integração BigQuery **pulados** (sem credenciais), por design.
- Cobertura 70% no total; módulos críticos (quality, gold, silver, streaming
  core) entre 80% e 100%. Módulos 0% são exclusivamente os de nuvem
  (`bigquery_client`, `bronze/loader` de carga, `main`), não exercitáveis offline.

## Tabelas

- **Offline materializadas (Parquet):** Bronze `uf`, Silver `uf` e produtos Gold
  quando há indicador. Município e demais dependem do BigQuery.
- **BigQuery:** não validado neste ambiente (B1).

## Contagens (entidade UF, execução offline)

`bronze = 27`, `válidos = 27`, `inválidos = 0`, `silver = 27`. Invariantes OK.

## Arquivos gerados (locais, fora do Git)

`data/bronze/`, `data/silver/`, `data/audit/` (relatórios + JSONL). Nenhum é
versionado (ver `.gitignore`).

## Streaming

Lógica (validação, deduplicação, microbatch, quarentena) validada por 9 testes.
Execução ao vivo requer Docker (B2).

## Problemas conhecidos e limitações

- B1 (BigQuery) e B2 (Docker) — ver `docs/blockers.md`.
- Fontes educacionais não validadas — ver `docs/source_limitations.md`.

## Itens concluídos

Fases 0–16 implementadas: qualidade, Silver, framework Batch, integração, Gold,
streaming, CLI, observabilidade, FinOps, segurança, testes, CI, Docker e
documentação.

## Itens opcionais / pendentes de ação humana

- Autenticar o BigQuery e habilitar as fontes educacionais reais.
- Subir o Docker e executar o streaming ao vivo.
- Materializar as tabelas em nuvem e gravar o vídeo.

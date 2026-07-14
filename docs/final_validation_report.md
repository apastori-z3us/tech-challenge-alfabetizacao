# Relatório de Validação Final

- **Data:** 2026-07-14
- **Branch:** `feature/validacao-fontes-reais` (a mesclar em `develop`/`main`)
- **Ambiente:** Windows 11, PowerShell, Python 3.12.10, venv do projeto
- **Docker:** Desktop 29.6.1 (engine linux) — streaming executado ao vivo
- **BigQuery:** projeto `rising-reserve-352718` (Sandbox), 4 datasets acessíveis
- **Aluna:** Ana Beatriz Pastori dos Santos — RM 372884

## Diagnóstico dos bloqueios (resolvidos)

- **BigQuery (TLS):** inspeção do **Norton Web/Mail Shield** reassinava o HTTPS;
  o `certifi` não confiava na raiz Norton. Resolvido com bundle combinado
  (certifi + raízes do Windows) apontado por `custom_ca_certs_file` e variáveis
  `*_CA_BUNDLE` no `.env`. **Sem** desabilitar verificação.
- **Docker:** Desktop estava fechado; iniciado e validado.

## Comandos executados e resultados

| Comando | Resultado |
| --- | --- |
| `bq ls` + 4 `bq ls tc_alfabetizacao_*` | ✅ 4 datasets, tabelas materializadas |
| `python -m src.cli batch` | ✅ 7 fontes → Bronze (Parquet + BQ) |
| `python -m src.cli silver` | ✅ 7 entidades → Silver (BQ) |
| `python -m src.cli gold` | ✅ 5 produtos → Gold (BQ) |
| `python -m src.cli all` | ✅ EXIT 0 (pipeline completo) |
| `python -m src.cli audit-sync` | ✅ pipeline_runs + quality_results no BQ |
| `docker compose up -d redpanda` + stream | ✅ 20 válidos + casos de borda |
| `python -m ruff check .` | ✅ All checks passed |
| `python -m pytest -m "not integration"` | ✅ 43 passed |
| `python -m pytest -m integration` (RUN_BQ_INTEGRATION=1) | ✅ 2 passed |
| `python -m pytest --cov=src` | ✅ cobertura 70% |
| `docker compose config --quiet` | ✅ válido |
| `python -m pip check` | ✅ sem conflitos |

## Tabelas (BigQuery)

- **Bronze (7):** municipio, uf, meta_brasil, meta_uf, meta_municipio,
  indicador_alfabetizacao, aluno.
- **Silver (7):** idem.
- **Gold (5):** indicador_municipio_ano, meta_vs_resultado, evolucao_temporal,
  resumo_uf, ml_features_municipio.
- **Audit (2):** pipeline_runs, quality_results (streaming_metrics local).

## Contagens

| Entidade | Bronze | Silver | Gold |
| --- | ---: | ---: | ---: |
| municipio | 5.571 | 5.571 | — |
| uf | 27 | 27 | — |
| meta_brasil | 3 | 3 | — |
| meta_uf | 79 | 79 | — |
| meta_municipio | 10.704 | 10.704 | — |
| indicador_alfabetizacao | 10.896 | 10.896 | indicador_municipio_ano 10.896 |
| aluno | 100.000 | 100.000 | — |
| resumo_uf | — | — | 25 |

Invariantes (`bronze = válidos + inválidos`, `válidos = silver`) OK; 0 inválidos
(dados oficiais limpos).

## Resultados analíticos

`status_meta`: NAO_ATINGIDA 7.734 · ATINGIDA 2.920 · SEM_META 242 (total 10.896).
Top UF por média: CE 90,14% · GO 76,44% · ES 75,85% · PR 74,95% · MG 68,96%.
Integridade: 0 órfãos, 100% match município↔UF, 242 resultados sem meta.

## Streaming

Sessão 1: 20 consumidos / 20 válidos / latência 10,27s / 1 microbatch.
Sessão 2 (borda): 6 / 2 válidos / 3 inválidos / 1 duplicado / 4 na quarentena.

## Testes / Cobertura / Lint

43 unitários + 2 integração (BQ) verdes; cobertura 70% (módulos críticos
80–100%); Ruff limpo; `pip check` ok; compose válido.

## CI (GitHub Actions)

Workflow `CI` (`.github/workflows/ci.yml`): Ruff + pytest sem BigQuery +
cobertura + validação YAML + `docker compose config`. Status confirmado após
push/PR (ver seção de PRs no `docs/pull_request_guide.md`).

## Anonimização / LGPD

`id_aluno` → hash SHA-256 na Silver; verificado ausência de PII; nenhum dado
pessoal na Gold.

## Limitações e pendências

- `aluno` como amostra anonimizada (L2); `resumo_uf` 25 UFs (L3); 242 sem meta
  (L4). Ver `docs/source_limitations.md`.
- **Pendências humanas:** revisar/mesclar PRs; gravar e publicar o vídeo.

## Status

**PRONTO PARA ENTREGA** (execução real validada em nuvem e streaming ao vivo;
resta a gravação do vídeo e a mesclagem dos PRs).

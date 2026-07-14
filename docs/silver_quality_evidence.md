# Evidência de Execução — Silver + Qualidade

- **Data:** 2026-07-14
- **Comando:** `python -m src.cli silver`
- **BigQuery:** `tc_alfabetizacao_silver` (7 tabelas) + `tc_alfabetizacao_audit`.

Invariantes verificados: `bronze_count = valid_count + invalid_count` e
`valid_count = silver_count`.

| Entidade | Bronze | Válidos | Inválidos | Silver (BQ) | Status |
| --- | ---: | ---: | ---: | ---: | :---: |
| municipio | 5.571 | 5.571 | 0 | 5.571 | ✅ |
| uf | 27 | 27 | 0 | 27 | ✅ |
| meta_brasil | 3 | 3 | 0 | 3 | ✅ |
| meta_uf | 79 | 79 | 0 | 79 | ✅ |
| meta_municipio | 10.704 | 10.704 | 0 | 10.704 | ✅ |
| indicador_alfabetizacao | 10.896 | 10.896 | 0 | 10.896 | ✅ |
| aluno | 100.000 | 100.000 | 0 | 100.000 | ✅ |

## Qualidade e quarentena

Os dados oficiais do INEP/diretórios chegaram **limpos** (0 registros inválidos)
após as regras de padronização (trim, UF em maiúsculo, tipos). O mecanismo de
quarentena está comprovado pelos testes unitários e pelo fluxo de streaming
(eventos inválidos/duplicados). Relatórios por execução em
`data/audit/quality/<entidade>/` e consolidado em `quality_results` (local e BQ).

## Anonimização de aluno (LGPD)

`id_aluno` é substituído por **hash SHA-256** (64 caracteres) já na padronização
Silver. As colunas Silver de `aluno` são: `ano, id_municipio, id_aluno(hash),
rede, serie, alfabetizado` + metadados. **Nenhum dado pessoal identificável** —
verificado programaticamente (sem colunas nome/cpf/endereço).

## Auditoria

`tc_alfabetizacao_audit.quality_results` (7 linhas — uma por entidade) e
`pipeline_runs` sincronizados via `python -m src.cli audit-sync`.

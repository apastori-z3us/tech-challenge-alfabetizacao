# Inventário de Fontes

Entidades obrigatórias do desafio e o estado de validação de cada uma. A
descoberta via `bq ls` / `bq show` **não pôde ser executada** neste ambiente
(BigQuery inacessível — ver `docs/blockers.md`). Por governança, nenhuma tabela
educacional teve o nome **inventado**; permanecem `enabled: false` até validação.

## Metodologia de descoberta (a executar quando o BigQuery estiver acessível)

```bash
bq ls basedosdados:
bq ls basedosdados:<DATASET>
bq show --schema --format=prettyjson basedosdados:<DATASET>.<TABELA>
# Consultas de descoberta sempre com colunas explícitas e LIMIT:
bq query --use_legacy_sql=false \
  'SELECT ano, id_municipio, <col> FROM `basedosdados.<DATASET>.<TABELA>` LIMIT 10'
```

Para cada fonte, coletar: project, dataset, table_id, descrição, granularidade,
período, volume aproximado, colunas/tipos, PK lógica, FKs, nulos, duplicidades,
cobertura territorial, compatibilidade temporal, dados sensíveis, custo estimado
e limitações.

## Estado das fontes

| Entidade | Fonte | Estado | Observação |
| --- | --- | --- | --- |
| Município | `basedosdados.br_bd_diretorios_brasil.municipio` | ✅ Validada | Fluxo Batch funcional |
| UF | Derivada de `municipio` + referência oficial | ✅ Derivada | Evita tabela não validada |
| Meta Brasil | a validar | ⛔ Pendente | `PREENCHER_APOS_VALIDACAO` |
| Meta UF | a validar | ⛔ Pendente | `PREENCHER_APOS_VALIDACAO` |
| Meta Município | a validar | ⛔ Pendente | `PREENCHER_APOS_VALIDACAO` |
| Indicador alfabetização | a validar | ⛔ Pendente | `PREENCHER_APOS_VALIDACAO` |
| Aluno | a validar | ⛔ Pendente | Dados sensíveis; exige anonimização |

## Município (validada)

- **project.dataset.table:** `basedosdados.br_bd_diretorios_brasil.municipio`
- **Granularidade:** 1 linha por município (≈ 5.570 municípios).
- **Colunas usadas:** `id_municipio` (STRING, 7 dígitos), `nome` (STRING),
  `sigla_uf` (STRING).
- **PK lógica:** `id_municipio`. **FK:** `sigla_uf` → UF.
- **Cobertura:** nacional. **Sensível:** não. **Custo:** baixo (poucas colunas).

## UF (derivada)

- Construída a partir das `sigla_uf` distintas do diretório de municípios,
  enriquecida com `codigo_uf` (IBGE), `nome` e `regiao` da referência oficial
  (`src/quality/reference.py`). 27 UFs. Decisão em `docs/source_limitations.md`.

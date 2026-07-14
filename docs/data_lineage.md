# Linhagem de Dados

Fluxo `fonte → Bronze → Silver → Gold` por entidade e produto analítico.

## Batch

```text
basedosdados.br_bd_diretorios_brasil.municipio
   → Bronze  (data/bronze/batch/municipio/ + tc_alfabetizacao_bronze.municipio)
   → Silver  (tc_alfabetizacao_silver.municipio)   [qualidade + padronização]
   → Quarentena (registros inválidos)

referência oficial de UFs + distinct(sigla_uf) da Bronze de municípios
   → Bronze  (uf, derivada)
   → Silver  (tc_alfabetizacao_silver.uf)

meta_brasil / meta_uf / meta_municipio / indicador_alfabetizacao / aluno
   → Bronze  → Silver   [pendentes de validação da fonte — ver source_limitations.md]
```

## Streaming

```text
Produtor (eventos sintéticos) → Redpanda (tópico) → Consumidor
   → validação de schema → deduplicação (event_id)
   → Bronze streaming (Parquet)  |  Quarentena (inválidos/duplicados)
   → microbatch → (Bronze BigQuery em lote) → Silver
```

## Linhagem por coluna dos produtos Gold

### `indicador_municipio_ano`

| Coluna | Origem |
| --- | --- |
| `taxa_alfabetizacao` | Silver `indicador_alfabetizacao` |
| `nome_municipio`, `sigla_uf` | Silver `municipio` |
| `regiao` | referência (`sigla_uf` → região) |
| `meta_municipal` | Silver `meta_municipio` |
| `diferenca_meta`, `percentual_atingimento`, `status_meta` | cálculo (`src/gold/build.py`) |

### `meta_vs_resultado`

Resultado (indicador) + `meta_municipio` + `meta_uf` + `meta_brasil` → diferenças
absolutas/percentuais e `status`.

### `evolucao_temporal`

`indicador_alfabetizacao` ordenado por localidade/ano → `variacao_anual`,
`variacao_acumulada`.

### `resumo_uf`

Agregação de `indicador_municipio_ano` por UF (+ `meta_uf`).

### `ml_features_municipio`

`indicador_municipio_ano` + `evolucao_temporal` → atributos para IA, **sem dados
pessoais**.

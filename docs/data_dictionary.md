# Dicionário de Dados

Nomenclatura padronizada usada nas camadas Silver e Gold. Renomeações em relação
às fontes são registradas aqui (nenhuma renomeação arbitrária sem registro).

## Renomeações reais (fonte → canônico)

| Fonte (real) | Coluna original | Coluna canônica |
| --- | --- | --- |
| br_bd_diretorios_brasil.uf | `id_uf` | `codigo_uf` |
| br_bd_diretorios_brasil.uf | `sigla` | `sigla_uf` |
| meta_alfabetizacao_* | `meta_alfabetizacao_2026` | `valor_meta` |

**Decisão:** `valor_meta` = `meta_alfabetizacao_2026` (meta projetada para 2026,
ano de referência do desafio). Os SQLs versionados em `sql/extraction/` aplicam
as renomeações explicitamente.

## Nomes canônicos

| Coluna | Tipo | Descrição |
| --- | --- | --- |
| `ano` | INTEGER | Ano de referência |
| `codigo_uf` | STRING | Código IBGE da UF (2 dígitos) |
| `sigla_uf` | STRING | Sigla da UF (2 letras, maiúsculas) |
| `id_municipio` | STRING | Código IBGE do município (7 dígitos) |
| `nome_municipio` | STRING | Nome do município |
| `regiao` | STRING | Região geográfica |
| `valor_meta` | FLOAT | Meta de alfabetização (0–100) |
| `taxa_alfabetizacao` | FLOAT | Taxa observada de alfabetização (0–100) |
| `rede` | STRING | Rede de ensino (ex.: pública, privada) |
| `serie` | STRING | Série/ano escolar |

## Município (Silver: `tc_alfabetizacao_silver.municipio`)

| Coluna | Tipo | Nulo | Origem |
| --- | --- | --- | --- |
| `id_municipio` | STRING | não | fonte |
| `nome` | STRING | não | fonte |
| `sigla_uf` | STRING | não | fonte (padronizada em maiúsculo) |
| `_quality_status` | STRING | não | Silver |
| `_silver_processed_timestamp` | STRING | não | Silver |
| `_ingestion_id` | STRING | não | Bronze |
| `_record_hash` | STRING | não | Bronze |

## UF (Silver: `tc_alfabetizacao_silver.uf`)

| Coluna | Tipo | Nulo | Origem |
| --- | --- | --- | --- |
| `codigo_uf` | STRING | não | referência |
| `sigla_uf` | STRING | não | derivada |
| `nome` | STRING | não | referência |
| `regiao` | STRING | não | referência |

## Metas e Indicador (Silver — schema esperado, pendente de validação)

| Tabela | Colunas de negócio | Chave lógica |
| --- | --- | --- |
| `meta_brasil` | `ano`, `valor_meta` | `ano` |
| `meta_uf` | `ano`, `sigla_uf`, `valor_meta` | `ano`+`sigla_uf` |
| `meta_municipio` | `ano`, `id_municipio`, `valor_meta` | `ano`+`id_municipio` |
| `indicador_alfabetizacao` | `ano`, `id_municipio`, `sigla_uf`, `taxa_alfabetizacao`, `rede`, `serie` | `ano`+`id_municipio` (+`rede`/`serie`) |
| `aluno` | `ano`, `id_aluno` (hash), `id_municipio`, `rede`, `serie` | `ano`+`id_aluno` |

Metadados Silver comuns: `_quality_status`, `_silver_processed_timestamp`,
`_ingestion_id`, `_record_hash`.

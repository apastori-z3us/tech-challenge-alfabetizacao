# Inventário de Fontes (validadas no BigQuery)

Todas as entidades obrigatórias foram **descobertas e validadas** no BigQuery
Sandbox (projeto público `basedosdados`). Descoberta via `bq ls` / `bq show` e
consultas com `LIMIT`.

## Fontes

| Entidade | project.dataset.table | Granularidade | Período | Linhas (fonte) |
| --- | --- | --- | --- | ---: |
| municipio | basedosdados.br_bd_diretorios_brasil.municipio | município | atemporal | 5.571 |
| uf | basedosdados.br_bd_diretorios_brasil.uf | UF | atemporal | 27 |
| meta_brasil | basedosdados.br_inep_avaliacao_alfabetizacao.meta_alfabetizacao_brasil | Brasil/ano | 2023–2025 | 3 |
| meta_uf | basedosdados.br_inep_avaliacao_alfabetizacao.meta_alfabetizacao_uf | UF/ano | 2023–2025 | 81 |
| meta_municipio | basedosdados.br_inep_avaliacao_alfabetizacao.meta_alfabetizacao_municipio | município/ano | 2023–2024 | 10.704 |
| indicador_alfabetizacao | basedosdados.br_inep_avaliacao_alfabetizacao.municipio | município/ano | 2023–2024 | 23.995 |
| aluno | basedosdados.br_inep_avaliacao_alfabetizacao.alunos | aluno/ano | 2023–2024 | 3.867.999 |

Fonte educacional: **INEP — Avaliação Nacional de Alfabetização** (dataset
`br_inep_avaliacao_alfabetizacao`), que reúne metas (Brasil/UF/município),
resultados (taxa de alfabetização) e microdados de alunos.

## Detalhes por entidade

### municipio (dimensão)
Colunas: `id_municipio` (STRING, 7 díg.), `nome`, `sigla_uf`. PK `id_municipio`.
FK `sigla_uf` → uf. Cobertura nacional. Sem dados sensíveis.

### uf (dimensão)
Colunas reais: `id_uf`, `sigla`, `nome`, `regiao` → renomeadas para
`codigo_uf`, `sigla_uf`, `nome`, `regiao`. PK `sigla_uf`. 27 UFs.

### meta_brasil / meta_uf / meta_municipio
Formato "largo" (`meta_alfabetizacao_2024..2030`). Selecionamos
`meta_alfabetizacao_2026` como `valor_meta`. Chaves: `ano`, (`ano`,`sigla_uf`),
(`ano`,`id_municipio`). Sem nulos após filtro. Valores 0–100.

### indicador_alfabetizacao (resultado)
Colunas: `ano`, `id_municipio`, `serie` (2º ano), `rede`, `taxa_alfabetizacao`
(0–100), além de `media_portugues` e proporções por nível. Filtro `rede='3'`
(Municipal) → chave única (`ano`,`id_municipio`), 5.448 municípios/ano.

### aluno (microdados)
Colunas: `ano`, `id_municipio`, `id_escola`, `id_aluno`, `serie`, `rede`,
`alfabetizado`, `proficiencia`, `peso_aluno`. **Dados sensíveis:** `id_aluno`
recebe **hash** na Silver; PII não trafega para a Gold. Amostra ingerida (ver
`source_limitations.md`).

## Custo / FinOps
Consultas com colunas explícitas, `LIMIT` na descoberta, `dry run`,
`maximum_bytes_billed` (1 GB) e cache. Ver `docs/finops.md`.

# Limitações das Fontes

Este documento registra, de forma transparente, toda decisão que envolve
limitação de dados (exigência do enunciado).

## L1 — Descoberta de fontes educacionais bloqueada

O BigQuery está inacessível neste ambiente (ver `docs/blockers.md`), portanto
**não foi possível** validar via `bq ls`/`bq show` os nomes reais das tabelas de
metas, indicador de alfabetização e microdados de alunos.

**Decisão:** essas fontes permanecem `enabled: false` em `config/sources.yaml`
com `table_id: PREENCHER_APOS_VALIDACAO`. **Nenhum nome foi inventado.** O
framework de ingestão é dirigido por configuração: basta validar o nome real,
preencher o `table_id` e habilitar a fonte para que o mesmo código a processe.

## L2 — UF como dimensão derivada

Em vez de assumir uma tabela de UF não validada, a dimensão UF é **derivada** do
diretório oficial de municípios (distinct `sigla_uf`) e enriquecida com
`codigo_uf` (IBGE), `nome` e `regiao` a partir de referência versionada em
`src/quality/reference.py`. Isso é determinístico e auditável.

## L3 — Compatibilidade temporal entre metas e resultados

O enunciado alerta que "dados de alunos" e o indicador podem ter períodos
diferentes das metas. **Decisão:** não haverá junção entre anos ou granularidades
incompatíveis. Quando os períodos não coincidirem, os dados serão mantidos em
**produtos analíticos separados**, com a limitação documentada, e o `status_meta`
receberá `SEM_META`/`SEM_RESULTADO` conforme o caso.

## L4 — Dados agregados vs. microdados

Caso a fonte de indicador exista apenas de forma agregada (município/UF/Brasil),
**não** serão simulados microdados de alunos em Batch. Dados sintéticos são
usados **apenas** para demonstrar o fluxo de Streaming, nunca para substituir
silenciosamente uma fonte obrigatória.

## L5 — Dados pessoais de alunos

Se a fonte de alunos for validada, `id_aluno` será submetido a hash e campos
pessoais desnecessários serão removidos já na Silver. **Nenhum dado pessoal
identificável chega à camada Gold** (ver `docs/security_and_governance.md`).

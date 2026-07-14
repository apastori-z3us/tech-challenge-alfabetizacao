# Limitações das Fontes

Toda decisão que envolve limitação de dados (exigência do enunciado). Após a
resolução dos bloqueios de BigQuery e Docker, as limitações abaixo são de
**natureza dos dados**, não de ambiente.

## L1 — Metas em formato "largo" → `valor_meta` = meta 2026

As tabelas `meta_alfabetizacao_*` do INEP trazem a taxa observada e colunas de
meta por ano-alvo (`meta_alfabetizacao_2024..2030`). Para o modelo canônico
(`ano`, chave, `valor_meta`), adotou-se **`valor_meta = meta_alfabetizacao_2026`**
(ano de referência do desafio). Registrado no dicionário de dados.

## L2 — `aluno`: amostra anonimizada

A fonte real de alunos tem **3.867.999 linhas**. Para demonstrar o fluxo de
privacidade sem custo/tempo excessivo, ingeriu-se uma **amostra** de `ano = 2024`
com `LIMIT 100000` (`sql/extraction/aluno.sql`). `id_aluno` é **anonimizado por
hash SHA-256** na Silver e **nenhum PII** vai para a Gold. Para ingestão integral,
remover o `LIMIT`. Isto **não substitui** a fonte — é a mesma fonte real, amostrada.

## L3 — `resumo_uf` com 25 UFs (não 27)

O produto Gold `resumo_uf` cobre apenas UFs com resultado de rede **Municipal**.
O Distrito Federal não possui rede municipal (não entra) e outra UF não teve
município com resultado no recorte 2023–2024. Não se fabricou dado ausente.

## L4 — 242 resultados sem meta municipal comparável

Dos 10.896 resultados município/ano, **242** não têm meta municipal correspondente
(mesmo ano e município). Esses recebem `status_meta = SEM_META`; não há join
forçado. Ver relatório de integridade em `docs/relationship_matrix.md`.

## L5 — Recorte do indicador

O indicador usa `serie = 2º ano` e `rede = Municipal` para obter chave única
(`ano`,`id_municipio`) e comparabilidade com a meta municipal. Outras redes/séries
existem na fonte e podem ser habilitadas ajustando `sql/extraction/indicador_alfabetizacao.sql`.

## L6 — Compatibilidade temporal

Metas e resultados coincidem em 2023–2024 (sem anos incompatíveis detectados:
`anos_incompativeis = []`). Caso surjam períodos divergentes, o pipeline não faz
join por ano incompatível e marca `SEM_META`/`SEM_RESULTADO`.

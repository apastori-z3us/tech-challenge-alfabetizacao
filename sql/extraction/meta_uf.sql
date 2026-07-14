SELECT
    ano,
    sigla_uf,
    meta_alfabetizacao_2026 AS valor_meta
FROM `basedosdados.br_inep_avaliacao_alfabetizacao.meta_alfabetizacao_uf`
WHERE meta_alfabetizacao_2026 IS NOT NULL
ORDER BY ano, sigla_uf

SELECT
    ano,
    id_municipio,
    meta_alfabetizacao_2026 AS valor_meta
FROM `basedosdados.br_inep_avaliacao_alfabetizacao.meta_alfabetizacao_municipio`
WHERE meta_alfabetizacao_2026 IS NOT NULL
ORDER BY ano, id_municipio

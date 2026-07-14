-- Meta de alfabetizacao nacional. valor_meta = meta projetada para 2026
-- (ano de referencia do desafio). Decisao documentada em data_dictionary.md.
SELECT
    ano,
    meta_alfabetizacao_2026 AS valor_meta
FROM `basedosdados.br_inep_avaliacao_alfabetizacao.meta_alfabetizacao_brasil`
WHERE meta_alfabetizacao_2026 IS NOT NULL
ORDER BY ano

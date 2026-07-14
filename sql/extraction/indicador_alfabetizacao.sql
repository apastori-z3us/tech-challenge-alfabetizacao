-- Resultado observado de alfabetizacao (2o ano EF, rede Municipal=3),
-- granularidade municipio/ano, para comparacao com a meta municipal.
SELECT
    ano,
    id_municipio,
    serie,
    rede,
    taxa_alfabetizacao
FROM `basedosdados.br_inep_avaliacao_alfabetizacao.municipio`
WHERE rede = '3' AND taxa_alfabetizacao IS NOT NULL
ORDER BY ano, id_municipio

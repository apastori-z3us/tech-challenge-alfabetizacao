SELECT
    CAST(id_uf AS STRING) AS codigo_uf,
    sigla AS sigla_uf,
    nome,
    regiao
FROM `basedosdados.br_bd_diretorios_brasil.uf`
WHERE id_uf IS NOT NULL
ORDER BY sigla_uf

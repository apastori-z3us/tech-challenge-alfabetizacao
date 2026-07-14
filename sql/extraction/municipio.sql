SELECT
    CAST(id_municipio AS STRING) AS id_municipio,
    nome,
    sigla_uf
FROM `basedosdados.br_bd_diretorios_brasil.municipio`
WHERE id_municipio IS NOT NULL
ORDER BY id_municipio
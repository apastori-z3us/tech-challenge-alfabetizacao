-- Microdados de alunos (amostra limitada e ANONIMIZADA para demonstrar o fluxo
-- de privacidade). id_aluno recebe hash na Silver; nenhum PII vai para a Gold.
-- Amostra: ano 2024. LIMITE documentado por FinOps/tempo (fonte real tem ~3,9M linhas).
SELECT
    ano,
    id_municipio,
    id_aluno,
    rede,
    serie,
    alfabetizado
FROM `basedosdados.br_inep_avaliacao_alfabetizacao.alunos`
WHERE ano = 2024 AND id_aluno IS NOT NULL
LIMIT 100000

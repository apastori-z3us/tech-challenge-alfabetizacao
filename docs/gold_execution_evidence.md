# Evidência de Execução — Gold (dados reais)

- **Data:** 2026-07-14
- **Comando:** `python -m src.cli gold`
- **BigQuery:** `tc_alfabetizacao_gold` (5 produtos).

| Produto | Registros (BQ) | Granularidade | Período | Status |
| --- | ---: | --- | --- | :---: |
| indicador_municipio_ano | 10.896 | município/ano | 2023–2024 | ✅ |
| meta_vs_resultado | 10.896 | município/ano | 2023–2024 | ✅ |
| evolucao_temporal | 10.896 | município/ano | 2023–2024 | ✅ |
| resumo_uf | 25 | UF | 2023–2024 | ✅ |
| ml_features_municipio | 10.896 | município/ano | 2023–2024 | ✅ |

`resumo_uf` traz 25 UFs (e não 27): apenas UFs com resultados de rede Municipal
compõem o produto — o Distrito Federal não possui rede municipal e outra UF não
apresentou município com resultado no recorte. Decisão documentada (não fabricar).

## Distribuição de `status_meta` (indicador_municipio_ano)

| status_meta | registros |
| --- | ---: |
| NAO_ATINGIDA | 7.734 |
| ATINGIDA | 2.920 |
| SEM_META | 242 |
| **Total** | **10.896** |

`SEM_META = 242` corresponde aos 242 resultados sem meta municipal comparável
(ver relatório de integridade). Não há `SEM_RESULTADO` porque o produto parte do
indicador observado.

## Integridade (antes/depois do join)

```text
municipios_orfaos: 0        | municipio_uf_match_pct: 100.0
metas_sem_municipio: 0      | resultados_sem_meta: 242
anos_incompativeis: []      | municipio_chaves_duplicadas: 0
```

O join indicador × meta é 1:1 lógico (ano, id_municipio); não houve multiplicação
de linhas (entrada e saída = 10.896).

## Consulta de exemplo (executada)

```sql
SELECT sigla_uf, media, qtd_municipios, percentual_atingiu
FROM `rising-reserve-352718.tc_alfabetizacao_gold.resumo_uf`
ORDER BY media DESC LIMIT 5;
-- CE 90.14 (368 mun., 85.87%) | GO 76.44 | ES 75.85 | PR 74.95 | MG 68.96
```

## Regras de negócio e tratamentos

- `diferenca_meta = taxa - meta`; `percentual_atingimento = taxa/meta*100`
  (divisão por zero protegida → NaN).
- `status_meta ∈ {ATINGIDA, NAO_ATINGIDA, SEM_META, SEM_RESULTADO}`.
- `ml_features_municipio` sem dados pessoais.
- Linhagem por coluna em `docs/data_lineage.md`.

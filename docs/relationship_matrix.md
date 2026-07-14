# Matriz de Relacionamentos

Relacionamentos entre entidades e as decisões arquiteturais que controlam as
junções na camada Gold. Junções só ocorrem quando chave, cardinalidade,
granularidade e período são compatíveis (`src/gold/integration.py`).

| Origem | Destino | Chave | Cardinalidade | Granularidade | Período | Decisão |
| --- | --- | --- | --- | --- | --- | --- |
| municipio | uf | `sigla_uf` | N:1 | município → UF | atemporal | Junção validada; órfãos isolados |
| meta_municipio | municipio | `id_municipio` | N:1 | município/ano | anual | Junção só se município existir |
| meta_uf | uf | `sigla_uf` | N:1 | UF/ano | anual | Junção validada |
| indicador | municipio | `id_municipio` | N:1 | município/ano | anual | Junção validada |
| indicador | meta_municipio | `ano`+`id_municipio` | 1:1 (lógico) | município/ano | anual | Só quando anos coincidem |
| aluno | municipio | `id_municipio` | N:1 | aluno/ano | anual | Sem chave válida ⇒ **não** relacionar |

## Resultados reais da integração (2026-07-14)

Execução sobre a Silver real (município 5.571, uf 27, indicador 10.896,
meta_municipio 10.704):

```text
municipios_orfaos: 0            municipio_uf_match_pct: 100.0
metas_sem_municipio: 0         resultados_sem_meta: 242
anos_incompativeis: []         municipio_chaves_duplicadas: 0
```

Join indicador × meta = 1:1 lógico (`ano`,`id_municipio`): entrada e saída =
10.896 (sem multiplicação de linhas).

## Validações executadas

- Município pertence a uma UF válida (órfãos → `municipios_orfaos`).
- Meta municipal possui município (`metas_sem_municipio`).
- Resultado possui meta comparável no mesmo ano (`resultados_sem_meta`).
- Anos incompatíveis entre indicador e meta (`anos_incompativeis_indicador_meta`).
- Chaves duplicadas por entidade (`*_chaves_duplicadas`).
- Percentual de correspondência (`match_percentage`).

## Tratamento de órfãos e incompatibilidades

Registros órfãos **não são descartados**: são isolados e contabilizados no
relatório de integridade. Quando os períodos de meta e resultado não coincidem,
não há junção por ano; o `status_meta` recebe `SEM_META`/`SEM_RESULTADO` e a
limitação é registrada em `docs/source_limitations.md`.

## Produtos Gold (Fase 6)

| Produto | Tabela | Regra de negócio |
| --- | --- | --- |
| 1 | `indicador_municipio_ano` | Taxa vs. meta municipal; `status_meta`; `percentual_atingimento` (divisão protegida) |
| 2 | `meta_vs_resultado` | Resultado vs. metas municipal/estadual/nacional; diferenças abs/pct |
| 3 | `evolucao_temporal` | Série por localidade; `variacao_anual` e `variacao_acumulada` |
| 4 | `resumo_uf` | Média, mediana, min, max, contagens e % que atingiu a meta |
| 5 | `ml_features_municipio` | Atributos para IA, **sem dados pessoais** |

Linhagem por coluna e SQL/regra estão em `docs/data_lineage.md`.

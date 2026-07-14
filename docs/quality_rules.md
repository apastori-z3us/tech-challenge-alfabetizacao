# Regras de Qualidade de Dados

O framework de qualidade é **declarativo e reutilizável**: cada entidade define
uma `EntityQualitySpec` (colunas obrigatórias, padronizações, regras de linha e
chaves únicas) e o motor genérico `run_quality` (`src/quality/checks.py`) executa,
separa os registros e produz um `QualityReport`.

## Severidades

| Severidade | Efeito |
| --- | --- |
| `CRITICAL` | Falha de schema (coluna obrigatória ausente) → **interrompe** a transformação (`CriticalSchemaError`). |
| `ERROR` | Registro inválido → enviado à **quarentena**, sem interromper o lote. |

## Classificação dos registros

- **Válidos:** passam por todas as regras → camada Silver.
- **Inválidos:** reprovam em ao menos uma regra de linha ou são duplicados →
  quarentena (`data/quarantine/<entidade>/processing_date=YYYY-MM-DD/`).
- **Erros críticos de schema:** ausência de coluna obrigatória → exceção.

Invariantes garantidos pela carga Silver (`src/silver/loader.py`):

```text
bronze_count == valid_count + invalid_count
valid_count  == silver_loaded_count   (quando há carga no BigQuery)
```

## Regras — Município

| Regra | Coluna | Descrição |
| --- | --- | --- |
| `id_municipio.not_null` | id_municipio | Obrigatório |
| `id_municipio.seven_digits` | id_municipio | Exatamente 7 dígitos |
| `nome.not_null` | nome | Obrigatório |
| `sigla_uf.not_null` | sigla_uf | Obrigatória |
| `sigla_uf.valid_uf` | sigla_uf | Pertence às 27 UFs |
| `unique.id_municipio` | id_municipio | `id_municipio` único |

Padronizações aplicadas: remoção de espaços excedentes (`nome`, `id_municipio`),
`sigla_uf` em maiúsculo. Tipos padronizados como texto para as chaves.

## Regras — UF (Fase 4)

`sigla_uf` válida e única, `codigo_uf` de 2 dígitos, `nome` obrigatório.

## Regras — Metas (Brasil / UF / Município) (Fase 4)

`ano` obrigatório e numérico; `valor_meta` numérico em faixa válida (0–100);
unicidade por (`ano`), (`ano`,`sigla_uf`) ou (`ano`,`id_municipio`);
integridade referencial com UF/Município.

## Regras — Indicador (Fase 4)

`ano` obrigatório; territorialidade válida; `taxa_alfabetizacao` entre 0 e 100;
`rede`/`serie` quando presentes; chave lógica documentada no dicionário de dados.

## Regras — Aluno (Fase 4)

Schema real da fonte; anonimização/hash de identificadores; remoção de campos
pessoais desnecessários; **nenhum dado pessoal identificável na Gold**.

## Saídas por execução

- Silver Parquet: `data/silver/<entidade>/processing_date=YYYY-MM-DD/`
- Quarentena Parquet: `data/quarantine/<entidade>/processing_date=YYYY-MM-DD/`
- Relatório JSON: `data/audit/quality/<entidade>/<quality_run_id>.json`
- Auditoria consolidada: `data/audit/quality_results.jsonl`

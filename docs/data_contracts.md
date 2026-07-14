# Contratos de Dados

Cada fonte declara um contrato em `config/sources.yaml` (`expected_schema`),
consumido por `src/batch/models.py` (`ColumnContract`). O contrato define as
colunas esperadas, os tipos e a nulabilidade, servindo de base para as
verificações críticas de schema na ingestão e na qualidade.

## Formato do contrato

```yaml
expected_schema:
  <coluna>:
    type: STRING | INTEGER | FLOAT | TIMESTAMP
    nullable: true | false
```

## Regras de contrato

1. **Colunas mínimas.** A extração exige que todas as `selected_columns` estejam
   presentes; ausência interrompe a ingestão.
2. **Chave lógica.** Toda `key_column` deve estar em `selected_columns`
   (validado em `SourceConfig.validate()`).
3. **Schema crítico na Silver.** Ausência de coluna obrigatória levanta
   `CriticalSchemaError` (não prossegue após falha de schema).
4. **Metadados.** A Bronze acrescenta `_ingestion_id`, `_ingestion_timestamp`,
   `_source_project/_source_dataset/_source_table`, `_load_type`, `_record_hash`,
   `_schema_version`. A Silver acrescenta `_quality_status` e
   `_silver_processed_timestamp`.
5. **Versão.** `schema_version` acompanha cada fonte; mudanças de schema exigem
   incremento e atualização do dicionário de dados.

## Contratos por entidade

Os contratos vigentes estão em `config/sources.yaml`. Município e UF possuem
contrato validado; metas, indicador e aluno possuem contrato **esperado**
(pendente de validação da fonte real — ver `docs/source_limitations.md`).

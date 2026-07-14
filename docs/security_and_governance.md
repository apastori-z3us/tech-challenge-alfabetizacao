# Segurança e Governança

## Segredos e credenciais

- `.env` está no `.gitignore` (não versionado). Modelo público em `.env.example`.
- Credenciais ADC (`application_default_credentials.json`, `service-account*.json`)
  são ignoradas pelo Git e **nunca** embutidas no código ou nas imagens Docker.
- O `compose.yaml` não contém credenciais; variáveis vêm do ambiente.
- Nenhuma chave de API no repositório.

## Minimização e dados pessoais (LGPD)

- **Seleção explícita de colunas**: só se ingere o necessário.
- **Anonimização de aluno**: `id_aluno` recebe hash SHA-256 já na padronização
  Silver (`src/quality/rules/aluno.py`); campos pessoais desnecessários são
  removidos.
- **Nenhum dado pessoal identificável na Gold**: os produtos analíticos operam
  em granularidade de município/UF/Brasil.
- Base legal e finalidade: uso educacional/estatístico de políticas públicas.

## Separação de camadas e quarentena

- Bronze (bruto) → Silver (validado) → Gold (analítico), com datasets distintos.
- Registros inválidos vão para **quarentena** (não são descartados nem
  promovidos), permitindo correção e reprocessamento auditável.

## Auditoria e linhagem

- Toda execução registra `pipeline_runs`, `quality_results` e
  `streaming_metrics` (ver `docs/monitoring.md`).
- Linhagem fonte → Bronze → Silver → Gold em `docs/data_lineage.md`.

## Controle de acesso (conceitual)

- Datasets por camada permitem conceder acesso mínimo por papel (ex.: analistas
  leem apenas Gold; engenharia acessa Bronze/Silver).
- Em produção, recomenda-se IAM por dataset e views autorizadas para a Gold.

## Retenção e descarte

- Histórico canônico em Parquet particionado por data; Sandbox mantém snapshot.
- Dados de quarentena têm caráter temporário para diagnóstico.
- Identificadores pessoais não são retidos em claro em nenhuma camada persistida.

## Integridade

- Invariantes de contagem (`bronze = válidos + inválidos`;
  `válidos = carregados`) impedem perda ou duplicação silenciosa.
- Hash de registro (`_record_hash`) detecta alterações e duplicidades.

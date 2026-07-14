# Bloqueios e Limitações de Ambiente

Este documento registra, de forma transparente, os bloqueios encontrados durante
a execução do Tech Challenge e como o projeto os contornou **sem inventar
resultados**.

## B1 — BigQuery inacessível (autenticação)

**Sintoma**

```text
$ bq ls
ERROR: (bq) There was a problem refreshing your current auth tokens:
[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed:
unable to get local issuer certificate
Please run: gcloud auth login
```

**Causa provável:** token ADC expirado e/ou inspeção TLS corporativa que impede a
validação do certificado de `oauth2.googleapis.com`.

**Impacto:** neste ambiente **não foi possível**:
- executar `bq ls` / `bq show` para descoberta de fontes;
- rodar consultas reais na Base dos Dados;
- carregar tabelas no BigQuery Sandbox;
- executar `python -m src.main` até o fim (a etapa de conexão BQ falha).

**Mitigação aplicada (sem fabricar dados):**
- Toda leitura de dados foi tornada **injetável** (`DataReader`). Em produção usa
  BigQuery; em testes/execução offline usa Parquet local ou fixtures pequenas.
- O núcleo de qualidade, Silver, Gold e Streaming é **100% testável offline**.
- Nomes de tabelas de fontes educacionais **não foram inventados**: permanecem
  `enabled: false` em `config/sources.yaml` até validação real. Ver
  `docs/source_limitations.md`.

**Ação humana necessária para desbloquear:**
```powershell
gcloud auth login
gcloud config set project rising-reserve-352718
gcloud auth application-default login
# Se houver inspeção TLS corporativa, apontar o CA bundle:
#   setx GOOGLE_API_USE_CLIENT_CERTIFICATE false
#   $env:REQUESTS_CA_BUNDLE / $env:SSL_CERT_FILE = <caminho do CA corporativo>
bq ls
```

## B2 — Docker daemon indisponível

**Sintoma**

```text
failed to connect to the docker API at npipe:////./pipe/dockerDesktopLinuxEngine;
check if the path is correct and if the daemon is running
```

**Impacto:** não foi possível subir Redpanda nem executar `docker compose up`.

**Mitigação aplicada:**
- `Dockerfile` e `compose.yaml` implementados e validáveis via `docker compose config`.
- Lógica de streaming (validação de schema, deduplicação, microbatch, quarentena)
  implementada de forma desacoplada do broker e coberta por testes que **não
  exigem** Kafka.

**Ação humana necessária:** iniciar o Docker Desktop e executar:
```powershell
docker compose up -d redpanda
python -m src.cli stream-producer --events 20 --interval 2
python -m src.cli stream-consumer
docker compose down
```

## Princípios seguidos diante dos bloqueios

1. Investigar e registrar o erro real (acima).
2. Preservar o trabalho já existente (fluxo Batch de municípios intacto).
3. Oferecer alternativa compatível (execução offline injetável).
4. **Não** inventar nomes de fontes, contagens ou resultados de execução.
5. **Não** esconder a limitação — ela está no README e nos relatórios finais.

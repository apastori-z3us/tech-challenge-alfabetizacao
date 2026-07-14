# Bloqueios e Limitações de Ambiente

Registro transparente dos bloqueios encontrados e como foram **resolvidos**.

## B1 — BigQuery inacessível (TLS) — ✅ RESOLVIDO

**Sintoma:** `bq ls` e o cliente Python falhavam com
`[SSL: CERTIFICATE_VERIFY_FAILED] unable to get local issuer certificate` ao
renovar tokens em `oauth2.googleapis.com`.

**Causa (investigada):** a máquina executa **Norton AntiVirus "Web/Mail Shield"**,
que faz **inspeção TLS** e reassina o tráfego HTTPS com a CA
`CN=Norton Web/Mail Shield Root`. O Windows confia nessa raiz (por isso o
navegador e o `git` funcionam), mas Python/gcloud usam o bundle do `certifi`,
que **não** inclui a raiz Norton → falha de verificação.

**Solução aplicada (segura, sem desabilitar verificação):**
1. Exportadas as raízes confiáveis do Windows (`Cert:\LocalMachine\Root` +
   `CurrentUser\Root`) para um PEM.
2. Combinadas com o `certifi` em `C:\Users\Z3USAI\corp_ca_bundle.pem`.
3. Apontado o gcloud (`gcloud config set core/custom_ca_certs_file ...`) e as
   variáveis `REQUESTS_CA_BUNDLE`/`SSL_CERT_FILE`/`GRPC_DEFAULT_SSL_ROOTS_FILE_PATH`
   (no `.env`, fora do Git) para esse bundle.

**Resultado:** `bq ls`, consultas e o cliente Python passaram a funcionar; os 4
datasets ficaram acessíveis e todo o pipeline foi materializado no BigQuery.

> Observação: o bundle e as variáveis são **específicos desta máquina** e ficam
> fora do repositório. Em outro ambiente, autenticar normalmente
> (`gcloud auth login` / `application-default login`).

## B2 — Docker daemon indisponível — ✅ RESOLVIDO

**Sintoma:** `docker ps` falhava com
`failed to connect to the docker API ... dockerDesktopLinuxEngine`.

**Causa:** Docker Desktop estava fechado.

**Solução:** iniciado o Docker Desktop; após o engine subir, `docker info`
respondeu e `docker compose up -d redpanda` funcionou. O streaming foi executado
ao vivo (ver `docs/streaming_execution_evidence.md`) e o broker encerrado com
`docker compose down`.

## Limitações remanescentes (documentadas)

- **aluno:** a fonte real tem ~3,9 milhões de linhas. Foi ingerida uma **amostra
  anonimizada** (ano 2024, `LIMIT 100000`) para demonstrar o fluxo de privacidade
  sem custo/tempo excessivo. Basta remover o `LIMIT` em `sql/extraction/aluno.sql`
  para ingestão integral. Ver `docs/source_limitations.md`.
- **valor_meta:** as metas do INEP vêm em formato "largo" (colunas por ano-alvo);
  adota-se `meta_alfabetizacao_2026` como `valor_meta` (ano de referência do
  desafio). Decisão documentada em `docs/data_dictionary.md`.

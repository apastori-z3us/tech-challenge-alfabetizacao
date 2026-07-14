# Checklist de Demonstração (telas e comandos)

Telas e comandos a mostrar durante o vídeo, em ordem.

## Preparação (antes de gravar)

- [ ] `.venv` ativo e `.env` configurado.
- [ ] Terminal PowerShell no diretório do projeto.
- [ ] VS Code aberto no repositório (mostrar estrutura de pastas).

## Sequência de telas

1. [ ] **Estrutura do projeto** — `src/`, `config/`, `docs/`, `tests/`.
2. [ ] **Configuração** — `python -m src.cli validate-config`.
3. [ ] **Batch** — `python -m src.cli batch --source uf`
       → mostrar Parquet em `data/bronze/batch/uf/ingestion_date=.../`.
4. [ ] **Silver + qualidade** — `python -m src.cli silver --entity uf`
       → mostrar `data/silver/uf/...` e o relatório em `data/audit/quality/uf/`.
5. [ ] **Quarentena** — provocar um registro inválido e mostrar
       `data/quarantine/...` (opcional).
6. [ ] **Gold** — `python -m src.cli gold` (comentar a lógica dos produtos).
7. [ ] **Testes** — `python -m pytest -q` (todos verdes) e cobertura.
8. [ ] **Lint** — `python -m ruff check .`.
9. [ ] **Monitoramento** — `python scripts/generate_monitoring_report.py`.
10. [ ] **Streaming (se Docker disponível)**:
        - `docker compose up -d redpanda`
        - `python -m src.cli stream-producer --events 20 --interval 2`
        - `python -m src.cli stream-consumer --max-events 20`
        - `docker compose down`
11. [ ] **BigQuery (se autenticado)** — `bq ls tc_alfabetizacao_bronze`.
12. [ ] **Git** — `git log --oneline --graph` (evolução por branches/commits).

## Encerramento

- [ ] Mencionar limitações honestas (BigQuery/Docker) e ação humana.
- [ ] Reforçar nome e RM.

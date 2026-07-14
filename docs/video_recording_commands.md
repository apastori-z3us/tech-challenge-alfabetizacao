# Comandos para Gravação do Vídeo (ordem exata)

Ambiente: PowerShell, `.venv` ativo, `.env` configurado, BigQuery autenticado,
Docker Desktop em execução.

## 1. Validar configuração
```powershell
python -m src.cli validate-config
```

## 2. Executar o pipeline completo (Batch → Silver → Gold → Auditoria)
```powershell
python -m src.cli all
```

## 3. Mostrar as tabelas no BigQuery
```powershell
bq ls tc_alfabetizacao_bronze
bq ls tc_alfabetizacao_silver
bq ls tc_alfabetizacao_gold
bq ls tc_alfabetizacao_audit
```

## 4. Consulta analítica de exemplo
```powershell
bq query --use_legacy_sql=false `
 "SELECT sigla_uf, media, percentual_atingiu FROM `rising-reserve-352718.tc_alfabetizacao_gold.resumo_uf` ORDER BY media DESC LIMIT 5"
```

## 5. Monitoramento
```powershell
python scripts/generate_monitoring_report.py
```

## 6. Testes e lint
```powershell
python -m pytest -q
python -m ruff check .
```

## 7. Streaming ao vivo
```powershell
docker compose up -d redpanda
# aguardar "healthy":
docker compose ps
python -m src.cli stream-producer --events 20 --interval 1
python -m src.cli stream-consumer --max-events 20
docker compose down
```

## 8. Histórico Git
```powershell
git log --oneline --graph --decorate -15
```

> Dica: para a demonstração ficar dentro de 5 minutos, o `python -m src.cli all`
> pode ser pré-executado; no vídeo, focar em mostrar as tabelas, a consulta
> analítica, a quarentena do streaming e o histórico de commits.

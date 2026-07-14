# Roteiro do Vídeo Executivo (até 5 minutos)

Linguagem executiva, foco em valor e arquitetura — sem explicar código linha a
linha.

## 0:00–0:30 — Apresentação

- "Olá, sou Ana Beatriz Pastori dos Santos, RM 372884."
- Tema: **Pipeline Híbrido para Análise da Alfabetização no Brasil**.

## 0:30–1:10 — Problema de negócio

- Importância da alfabetização como indicador de política pública.
- Dados dispersos, em granularidades diferentes (município, UF, Brasil).
- Necessidade de integrar resultados e metas de forma confiável.

## 1:10–2:10 — Arquitetura

- Arquitetura Medalhão: Bronze, Silver, Gold.
- Dois fluxos: **Batch** (Base dos Dados) e **Streaming** (Redpanda local).
- Mostrar o diagrama Mermaid do README.

## 2:10–3:10 — Demonstração

- `python -m src.cli all` (batch → silver → gold) para a entidade UF.
- Mostrar Parquet gerado, tabela Bronze/Silver, relatório de qualidade e
  quarentena.
- Comentar os invariantes de contagem.

## 3:10–4:00 — Monitoramento, auditoria e FinOps

- `python scripts/generate_monitoring_report.py`.
- Auditoria (pipeline_runs / quality_results / streaming_metrics).
- Custo zero: Sandbox, dry run, `maximum_bytes_billed`, Parquet/Snappy.

## 4:00–4:40 — Valor para políticas públicas

- Comparar resultado vs. meta municipal/estadual/nacional.
- Evidenciar desigualdades regionais e municípios que atingiram a meta.

## 4:40–5:00 — IA e conclusão

- Como a Gold habilita predição/classificação (`ml_features_municipio`).
- Encerramento: governança, testes, CI e documentação completa.

> Observação honesta a mencionar: no ambiente de gravação, BigQuery e Docker
> podem exigir autenticação/daemon; o fluxo offline (UF) demonstra a pipeline
> ponta a ponta.

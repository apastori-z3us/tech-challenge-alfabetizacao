# Tech Challenge – Fase 2

## Pipeline Híbrido para Análise da Alfabetização no Brasil

**Aluna:** Ana Beatriz Pastori dos Santos  
**RM:** 372884  
**Fase:** 2  

## Contexto

Este projeto implementa uma pipeline híbrida de engenharia de dados
para análise da alfabetização no Brasil.

A solução integra processamento Batch e Streaming, organizando os
dados nas camadas Bronze, Silver e Gold da Arquitetura Medalhão.

## Tecnologias

- Python
- BigQuery Sandbox
- Docker
- Redpanda
- Pandas
- Parquet
- GitHub
- Pytest

## Arquitetura inicial

- BigQuery Sandbox como componente de nuvem;
- Python para extração e transformação;
- Parquet para preservação local;
- Docker e Redpanda para simulação de streaming;
- GitHub para versionamento e Pull Requests.

## Camadas

### Bronze

Armazena os dados brutos recebidos das fontes Batch e Streaming.

### Silver

Armazena os dados tratados, padronizados, validados e integrados.

### Gold

Armazena os produtos analíticos preparados para consultas,
dashboards, estatística e inteligência artificial.

## Autora

Ana Beatriz Pastori dos Santos — RM 372884.
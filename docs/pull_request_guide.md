# Guia de Pull Requests

O GitHub CLI (`gh`) não está instalado neste ambiente; as branches são enviadas
por push e os PRs abertos manualmente na interface do GitHub.

## Fluxo Git seguido

- `main` e `develop` preservados; sem force push; sem reescrita de histórico.
- Branches de funcionalidade por conjunto de fases; commits pequenos e descritivos.

## Branches da finalização real

| Branch | Conteúdo | Destino |
| --- | --- | --- |
| `feature/validacao-fontes-reais` | Fontes reais, SQL, Batch/Silver/Gold, audit-sync, testes | `develop` |
| `docs/entrega-final` | Evidências de execução + documentação final atualizada | `develop` |

Branches anteriores (fases 0–16) permanecem publicadas como histórico.

## PRs sugeridos

### PR 1 — Validação de fontes e materialização do pipeline
- **Head:** `feature/validacao-fontes-reais` → **Base:** `develop`
- **Descrição:** valida fontes educacionais reais (INEP), habilita `sources.yaml`,
  executa Batch/Silver/Gold no BigQuery, anonimiza `aluno`, sincroniza auditoria.
- **Evidências:** `docs/batch_execution_evidence.md`,
  `docs/silver_quality_evidence.md`, `docs/gold_execution_evidence.md`.
- **Testes:** 43 unitários + 2 integração; Ruff limpo.

### PR 2 — Streaming ao vivo, integração e documentação final
- **Head:** `docs/entrega-final` → **Base:** `develop`
- **Descrição:** evidência do streaming ao vivo (Redpanda), integração validada,
  relatório final, checklist e roteiro do vídeo.
- **Evidências:** `docs/streaming_execution_evidence.md`,
  `docs/final_validation_report.md`, `docs/delivery_checklist.md`.

## Comandos (quando houver `gh`)

```bash
gh pr create --base develop --head feature/validacao-fontes-reais \
  --title "Valida fontes educacionais e materializa pipeline completo" \
  --body-file docs/final_validation_report.md
gh pr create --base develop --head docs/entrega-final \
  --title "Streaming ao vivo, integração e documentação final" \
  --body-file docs/streaming_execution_evidence.md
```

## Envio das branches

```bash
git push -u origin feature/validacao-fontes-reais
git push -u origin docs/entrega-final
```

Após o push, o **GitHub Actions (CI)** roda em cada PR; mesclar apenas com CI
verde. Depois: `develop` → `main`.

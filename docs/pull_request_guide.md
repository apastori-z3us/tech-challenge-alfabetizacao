# Guia de Pull Requests

O GitHub CLI (`gh`) não está instalado/autenticado neste ambiente, portanto as
branches são **enviadas por push** e os PRs devem ser abertos manualmente na
interface do GitHub. As branches são **empilhadas** (cada uma parte da anterior),
o que mantém o diff de cada PR restrito à sua fase.

## Fluxo Git seguido

- `main` e `develop` preservados; `develop` avançou para `main` por
  **fast-forward** (sem reescrever histórico, sem force push).
- Uma branch por conjunto de fases; commits pequenos e descritivos.

## Ordem de merge sugerida

`feature/silver-quality` → `feature/data-sources-batch` →
`feature/gold-analytics` → `feature/streaming-redpanda` →
`feature/observability-finops` → `docs/final-documentation` → **develop** → **main**.

## PRs

| # | Branch (origem) | Destino | Título | Fases |
| --- | --- | --- | --- | --- |
| 1 | `feature/silver-quality` | `develop` | feat: qualidade e Silver de municípios | 0–1 |
| 2 | `feature/data-sources-batch` | `feature/silver-quality` | feat: catálogo de fontes e batch configurável | 2–3 |
| 3 | `feature/gold-analytics` | `feature/data-sources-batch` | feat: integração e produtos Gold | 4–6 |
| 4 | `feature/streaming-redpanda` | `feature/gold-analytics` | feat: streaming local com Redpanda | 7 |
| 5 | `feature/observability-finops` | `feature/streaming-redpanda` | feat: CLI, observabilidade, FinOps e CI | 8–12 |
| 6 | `docs/final-documentation` | `feature/observability-finops` | docs: documentação final | 13–16 |

Para cada PR incluir:

- **Descrição:** objetivo da fase e principais mudanças.
- **Arquivos:** ver `git diff --stat <base>..<branch>`.
- **Testes:** `python -m pytest -q` (40 verdes) e `python -m ruff check .`.
- **Evidências:** saída da CLI e/ou relatório de monitoramento.

## Comandos para abrir os PRs (quando houver `gh`)

```bash
gh pr create --base develop --head feature/silver-quality \
  --title "feat: qualidade e Silver de municípios" --body-file docs/quality_rules.md
# ... repetir para as demais branches conforme a tabela acima
```

## Envio das branches

```bash
git push -u origin feature/silver-quality
git push -u origin feature/data-sources-batch
git push -u origin feature/gold-analytics
git push -u origin feature/streaming-redpanda
git push -u origin feature/observability-finops
git push -u origin docs/final-documentation
git push -u origin develop
```

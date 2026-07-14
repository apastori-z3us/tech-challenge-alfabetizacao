# Guia de Pull Requests

O GitHub CLI (`gh`) não está instalado neste ambiente; as branches são enviadas
por push e os PRs são abertos manualmente na interface do GitHub.

## Estado atual da integração

Os **commits técnicos já foram integrados na `main`** (e em `develop`),
preservando o histórico e **sem force push**. Em especial:

- `feat: valida fontes educacionais reais e materializa pipeline completo` (`29d41c8`)
- `docs: evidencias de execucao real e documentacao final` (`f56dd38`, tip da `main`)

As branches de funcionalidade anteriores (`feature/*`, `docs/*`) permanecem
publicadas como histórico. Portanto, **não há PR técnico pendente** para a
materialização do pipeline — isso já está na `main`.

## PRs finais (a criar)

Restam apenas dois PRs de **fechamento**, contendo ajustes finais de
documentação/CI e a entrega do vídeo:

### PR final A — Ajustes de documentação e CI
- **Head:** `docs/validacao-final-ci` → **Base:** `main`
- **Conteúdo:** correções do relatório de validação, checklist de entrega e
  guia de PRs (este arquivo); nenhuma mudança de regra de negócio, pipeline,
  fontes ou tabelas.

### PR final B — Vídeo e entrega final
- **Head:** `docs/video-entrega-final` → **Base:** `main`
- **Conteúdo:** vídeo executivo (link/anexo), roteiro e checklist de gravação
  finalizados. *(Branch a ser criada quando o vídeo estiver pronto.)*

## Comandos (quando houver `gh`)

```bash
gh pr create --base main --head docs/validacao-final-ci \
  --title "Ajustes finais de documentacao e CI" \
  --body-file docs/final_validation_report.md
gh pr create --base main --head docs/video-entrega-final \
  --title "Video executivo e entrega final" \
  --body-file docs/video_script.md
```

## Envio das branches

```bash
git push -u origin docs/validacao-final-ci
# docs/video-entrega-final: criar e enviar quando o vídeo estiver pronto
```

## Após abrir os PRs

1. Aguardar o **GitHub Actions (CI)** rodar em cada PR.
2. Confirmar o status **verde** na aba *Actions* (evidência real).
3. Mesclar apenas com CI verde. Sem force push; histórico preservado.

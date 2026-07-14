# Aplicações em Inteligência Artificial

A camada Gold foi desenhada para habilitar IA **sem** exigir treinamento no
escopo deste desafio. O produto `ml_features_municipio` reúne atributos
agregados, **sem dados pessoais**.

## Casos de uso

- **Predição da taxa de alfabetização** do ano seguinte (regressão).
- **Classificação de risco** de não atingir a meta (binária).
- **Clusterização** de municípios por perfil de desempenho.
- **Detecção de anomalias** em séries temporais de taxa.
- **Priorização de políticas públicas** por lacuna para a meta.

## Alvos possíveis

- `taxa_alfabetizacao_ano_seguinte` (regressão).
- `atingira_meta` ∈ {0, 1} (classificação).

## Features possíveis (apenas quando disponíveis)

- histórico da taxa (`taxa_alfabetizacao`, `taxa_ano_anterior`);
- variação anual/acumulada;
- meta municipal/estadual/nacional e `diferenca_meta`;
- região e rede;
- série;
- indicadores socioeconômicos e de infraestrutura escolar (futuros).

## Interpretabilidade e riscos

- Preferir modelos interpretáveis (árvores, regressão logística) e explicações
  (ex.: importância de features, SHAP) para uso em política pública.
- **Viés:** dados regionais desiguais podem enviesar previsões; avaliar métricas
  por região/rede e evitar penalizar municípios já vulneráveis.
- **Dados de alunos:** nunca usar identificadores pessoais; features sempre
  agregadas. Anonimização a montante (Silver).
- **Validação humana:** resultados são apoio à decisão, não substituem análise
  de especialistas.

## Cuidado com dados insuficientes

Não treinar modelos com dados incompatíveis ou insuficientes só para "mostrar
IA". Enquanto as fontes de indicador/meta não forem validadas, mantém-se apenas
a **documentação** e a estrutura de features.

# Copa do Mundo 2026 — Simulador de Probabilidades

> Sistema de previsão combinando **ratings ELO, XGBoost e simulação Monte Carlo** para estimar a probabilidade de cada seleção conquistar a Copa do Mundo FIFA 2026 — atualizado em tempo real conforme os resultados oficiais chegam.

**[Acessar o app →](https://world-cup-2026-predictions-rhf.streamlit.app/)** &nbsp;|&nbsp; `Python` `XGBoost` `Monte Carlo` `Streamlit`

![Demo](assets/demo.gif)

---

## O problema

*"Quem vai ganhar a Copa?"* parece simples. Responder com rigor não é.

Três características tornam isso tecnicamente interessante:

**Incerteza composta.** Para ser campeã, uma seleção precisa vencer **seis jogos seguidos** contra adversários diferentes. Pequenas vantagens de qualidade se compõem de forma não-linear — um modelo que ignora isso subestima sistematicamente zebras e surpresas.

**Escassez de dados.** A Copa do Mundo Masculina tem apenas **964 jogos** em toda a sua história até 2022 — menos do que uma única temporada da Premier League. Qualquer engenharia de features complexa vai superajustar com esse volume.

**Não-estacionariedade.** O Brasil de 1970 não é o Brasil de 2026. Um modelo que trata todos os jogos históricos como equivalentes vai superestimar potências em declínio e subestimar seleções emergentes.

O projeto aborda os três com escolhas técnicas deliberadas, descritas na seção [Metodologia](#metodologia).

---

## Demo ao vivo

![Tela inicial](assets/home.jpg)

**[world-cup-2026-predictions-rhf.streamlit.app](https://world-cup-2026-predictions-rhf.streamlit.app/)**

O app tem quatro abas:

| Aba | Conteúdo |
|-----|---------|
| 🥇 Quem vai ganhar? | Progresso do torneio · próximos confrontos · ranking de probabilidades |
| 🔍 Minha seleção | Perfil da seleção · rating ELO · funil de probabilidades por fase |
| 🤔 Por que isso? | Ranking ELO · histórico ELO · importância de features · simulador de confronto direto |
| 📊 Posso confiar? | Métricas do modelo · metodologia · fontes de dados · limitações conhecidas |

---

## Arquitetura

```
app.py                       # Entry point do Streamlit
│
components/
├── data_loader.py           # Pipeline completo: load → ELO → treino → simulação
│                            # Resultados cacheados com @st.cache_data / @st.cache_resource
├── tab1_overview.py         # Aba visão geral do torneio
├── tab2_team.py             # Aba perfil da seleção
├── tab3_why.py              # Aba explicabilidade
├── tab4_trust.py            # Aba confiança no modelo
├── teams_2026.py            # Lista canônica das 48 seleções classificadas
├── flags.py                 # Seleção → URL da bandeira, código de 3 letras, cor nacional
└── theme.py                 # Tokens de design e helpers de tema Plotly
│
data/
├── fjelstul/matches.csv     # 964 jogos históricos — Copa Masculina 1930–2022
└── wc2026_matches.csv       # Resultados oficiais 2026 (atualizado conforme o torneio avança)
                             # Jogos não disputados armazenados com result="scheduled" (ignorados no ELO)
```

Sem banco de dados, sem arquivos de modelo serializados para produção, sem APIs externas. Tudo roda em memória a partir de dois CSVs. Adicionar um novo resultado ao `wc2026_matches.csv` atualiza o pipeline inteiro no próximo carregamento do app.

---

## Metodologia

### Etapa 1 — ELO Rating: medindo a força das seleções

Os ratings ELO são calculados sequencialmente a partir de todos os **1.061 jogos da Copa do Mundo Masculina** (1930–2026), incluindo os resultados oficiais de 2026 já integrados. O rating é atualizado após cada jogo:

```
rating[seleção_A] += K × (resultado − resultado_esperado)
```

- `K = 30` — equilibra memória histórica e responsividade a resultados recentes
- Rating base: **1.500** para seleções sem histórico em Copas
- Jogos não disputados da Copa 2026 ficam marcados como `result="scheduled"` e são ignorados no cálculo do ELO, evitando vazamento de dados

**Por que ELO e não o Ranking FIFA?** O Ranking FIFA usa critérios proprietários com pesos não documentados que mudaram entre edições. O ELO é completamente derivável a partir dos mesmos dados de jogos que o modelo usa — auditável e sem dependência externa.

### Etapa 2 — XGBoost: prevendo resultados individuais

Um classificador XGBoost multi-classe prevê o resultado de qualquer jogo: vitória do mandante (0), empate (1) ou vitória do visitante (2).

```python
features = ["elo_home", "elo_away", "elo_diff"]  # apenas três variáveis
```

A restrição é intencional: com ~1.060 amostras de treino, features adicionais aumentam variância sem reduzir viés. Três features simples com XGBoost regularizado superam modelos mais complexos na validação cruzada.

Uma Regressão Logística baseline é treinada em paralelo para quantificar o ganho real de complexidade:

| Modelo | Acurácia | vs. baseline aleatório |
|--------|----------|------------------------|
| **XGBoost** | **58%** | **+75%** |
| Regressão Logística | ~55% | +67% |
| Chute aleatório (3 classes) | 33% | — |

O XGBoost supera o baseline tanto em acurácia quanto em log-loss — as probabilidades geradas são mais calibradas, o que impacta diretamente a qualidade da simulação.

**Por que não uma rede neural?** Com ~1.060 amostras, qualquer modelo de alta capacidade vai superajustar. Testamos engenharia de features adicional (margem de gols, forma recente) e arquiteturas neurais — ganho marginal, variância maior. XGBoost com regularização é a escolha certa nesse regime de dados.

### Etapa 3 — Monte Carlo: simulando o torneio inteiro

A probabilidade de ser campeão não é a probabilidade de vencer um jogo. É a probabilidade de vencer **todos os jogos necessários**, contra adversários que também chegaram até lá.

O torneio é simulado **10.000 vezes**:

```
Para cada simulação:
  1. Monta o bracket com as seleções ainda vivas
  2. Para cada confronto: XGBoost gera P(vitória A), P(empate), P(vitória B)
  3. Sorteio ponderado determina o vencedor
  4. Avança para a próxima fase até restar uma seleção
  5. Registra qual seleção conquistou o título e chegou a cada fase

Resultado: P(campeã) = contagem de títulos / 10.000
```

Com 10.000 amostras, o erro estatístico fica abaixo de 1 ponto percentual por seleção. O pipeline completo — cálculo de ELO, treino do modelo e 10.000 simulações — roda em menos de 5 segundos.

**Por que Monte Carlo e não cálculo analítico?** Enumerar todos os caminhos possíveis no bracket cresce fatorialmente com o número de seleções. Monte Carlo com 10.000 amostras converge para erro <1% em milissegundos.

---

## Situação atual

*Torneio encerrado · 2026-07-19 · 104 resultados oficiais integrados*

| # ELO | Seleção | ELO* | Classificação final |
|-------|---------|------|---------------------|
| 9 | **Spain** | 1610 | 🏆 **Campeã** — 1×0 Argentina (após prorrogação) |
| 1 | Argentina | 1734 | 🥈 Vice-campeã — 0×1 Spain (após prorrogação) |
| 7 | England | 1622 | 🥉 3º lugar — 6×4 France |
| 2 | France | 1718 | 4º lugar — Semifinal — 0×2 Spain |

*\*ELO exibido é pré-quartas; o app recalcula em tempo real após cada resultado.*

---

## Como executar localmente

```bash
git clone https://github.com/rodrigohigashi/World_Cup_2026_predictions
cd World_Cup_2026_predictions
pip install -r requirements.txt
streamlit run app.py
```

Sem configuração adicional. O pipeline detecta automaticamente quais seleções ainda estão vivas a partir do CSV — adicionar um novo resultado ao `wc2026_matches.csv` atualiza o modelo inteiro.

**Requisitos:** Python 3.10+

---

## Estrutura do projeto

```
.
├── app.py
├── requirements.txt
├── assets/
│   ├── demo.gif
│   └── home.jpg
├── components/
│   ├── data_loader.py
│   ├── flags.py
│   ├── tab1_overview.py
│   ├── tab2_team.py
│   ├── tab3_why.py
│   ├── tab4_trust.py
│   ├── teams_2026.py
│   └── theme.py
├── data/
│   ├── fjelstul/            # Dados históricos de Copas (1930–2022)
│   └── wc2026_matches.csv   # Resultados ao vivo de 2026
├── notebooks/
│   └── copa2026.ipynb       # Análise exploratória e prototipagem do modelo
└── src/
    ├── build_dataset.py
    ├── download_data.py
    └── model.py
```

---

## Decisões técnicas

**ELO temporal sem decaimento.** Testamos um fator de decaimento que reduz o peso de jogos mais antigos. Nas validações retrospectivas (prever Copa N a partir das Copas 1 até N−1), o decaimento degradou a calibração. O intervalo de quatro anos entre torneios já funciona como filtro natural de obsolescência.

**Split treino/teste aleatório.** Um split temporal (treinar até 2014, testar em 2018 e 2022) seria metodologicamente mais rigoroso. Com ~1.060 amostras, o impacto prático nas métricas apresentadas é limitado — isso é documentado como limitação conhecida, não omitido.

**Sentinel `result="scheduled"`.** Jogos não disputados ficam no CSV com um valor sentinela e são ignorados no cálculo do ELO. Isso permite que `get_current_stage_matches()` derive os próximos confrontos automaticamente do mesmo arquivo, sem hardcode da estrutura do bracket.

**Sem serving de modelo externo.** O modelo é retreinado a cada cold start (~1 segundo). Isso evita drift de serialização — o modelo sempre reflete os dados de jogos mais recentes no CSV.

---

## Limitações conhecidas

Documentadas como parte da metodologia, não como rodapé de disclaimer:

- **ELO só de Copas** — Eliminatórias, Copa das Confederações e amistosos ficam de fora. Seleções que raramente se classificam têm histórico limitado e ratings menos confiáveis.
- **Pênaltis como 50/50** — Disputas por pênaltis são modeladas como sorteio. Há evidência de que algumas seleções têm vantagem estatística, mas o volume de dados por equipe é pequeno demais para modelar com confiança.
- **Bracket aleatório** — A estrutura real do bracket é substituída por sorteio em cada simulação. Isso subestima o impacto de cruzamentos favoráveis ou desfavoráveis.
- **Sem sinal de forma recente** — O ELO captura força histórica acumulada. Uma seleção em má fase no ano da Copa não tem esse sinal capturado.
- **Extrapolação do XGBoost em ELOs extremos** — Nas fases finais, seleções como Argentina (ELO 1734) e França (ELO 1726) atingem valores no percentil 97–99 da distribuição de treino. A análise SHAP confirmou que o modelo XGBoost produz previsões inconsistentes com a fórmula ELO clássica, com a Regressão Logística e com a base histórica nesses confrontos específicos (por exemplo, prevendo 24% de vitória para uma seleção com vantagem de +101 pontos de ELO, frente a uma taxa histórica de 71%). Uma abordagem híbrida baseada em Mean Leaf Sample Count (MLSC) para redirecionar casos extremos à Regressão Logística foi investigada e intencionalmente descartada: ela degradou consistentemente o desempenho na validação (maior log-loss, menor acurácia e pior calibração no conjunto de teste) em comparação com o XGBoost puro. O projeto mantém o XGBoost como único preditor e documenta esse comportamento como limitação conhecida, em vez de introduzir uma correção sem suporte empírico.

---

## Stack

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat&logo=python&logoColor=white)
![XGBoost](https://img.shields.io/badge/XGBoost-2.0+-FF6600?style=flat)
![Streamlit](https://img.shields.io/badge/Streamlit-1.35+-FF4B4B?style=flat&logo=streamlit&logoColor=white)
![Plotly](https://img.shields.io/badge/Plotly-5.18+-3F4F75?style=flat&logo=plotly&logoColor=white)
![scikit-learn](https://img.shields.io/badge/scikit--learn-1.3+-F7931E?style=flat&logo=scikitlearn&logoColor=white)

---

## Melhorias recentes

- Corrigida a distribuição de BYEs nas simulações Monte Carlo para garantir brackets estatisticamente uniformes.
- Adicionados testes unitários abrangentes para geração de bracket e lógica de simulação.
- Corrigido o mapeamento de fases do torneio para diferentes tamanhos de bracket.
- Eliminado o viés de mando de campo em jogos do mata-mata por meio de inferência simétrica, preservando o modelo XGBoost treinado.
- Expandida a cobertura de testes automatizados para prevenir regressões.

---

## Possíveis melhorias

- **Split temporal treino/teste** — Treinar nas Copas de 1930 a 2014, avaliar em 2018 e 2022
- **Modelagem de pênaltis** — Usar taxas históricas de conversão por seleção onde o tamanho da amostra permitir
- **Feature de forma recente** — Adicionar peso exponencialmente decrescente a jogos recentes dentro da atualização do ELO
- **Dados de eliminatórias** — Estender o ELO para incluir qualificatórias das seleções com histórico limitado em Copas
- **Simulação com bracket real** — Respeitar as regras reais de chaveamento (líderes de grupo vs. vice-líderes) em vez de sorteio

---

## Licença

Licença MIT — veja [LICENSE](LICENSE) para detalhes.

---

*Projeto por [Rodrigo Higashi](https://github.com/rodrigohigashi) · Copa do Mundo FIFA 2026*

# 🏆 Copa do Mundo 2026 — Simulador de Probabilidades

> Sistema de previsão que combina **ELO histórico + XGBoost + Monte Carlo** para estimar a probabilidade real de cada seleção conquistar o título — atualizado com os resultados oficiais da Copa em andamento.

**[🚀 Acessar o app →](https://world-cup-2026-predictions-rhf.streamlit.app/)** &nbsp;|&nbsp; `Python` `XGBoost` `Monte Carlo` `Streamlit`

---

## A pergunta que todo mundo faz — e por que é difícil de responder

*"Quem vai ganhar a Copa?"* parece simples. Executar rigorosamente não é.

Três problemas tornam esse projeto tecnicamente interessante:

**Incerteza composta.** Para ser campeã, uma seleção precisa vencer **6 jogos seguidos** contra adversários diferentes. Pequenas vantagens de qualidade se acumulam de forma não-linear — um modelo que ignora essa composição subestima sistematicamente zebras e surpresas.

**Escassez extrema de dados.** A Copa do Mundo tem apenas **964 jogos** em toda a história até 2022 — menos do que uma única temporada da Premier League. Qualquer arquitetura de feature engineering complexa vai superajustar ao ruído com esse volume.

**Não-estacionariedade.** O Brasil de 1970 não é o Brasil de 2026. Um modelo que trata todos os jogos históricos como equivalentes vai superestimar potências em declínio e subestimar seleções emergentes.

O projeto aborda os três com escolhas técnicas deliberadas — descritas na seção [Decisões técnicas](#decisões-técnicas).

---

## Resultado atual

*Atualizado após QF France × Morocco · 2026-07-11 · 97 resultados oficiais integrados*

**Brasil, Alemanha e Portugal foram eliminados ainda na fase de grupos.** O modelo atualizou os ELOs e rodou 10.000 novas simulações automaticamente após cada rodada.

| # ELO | Seleção | ELO atual | Fase atual |
|-------|---------|-----------|------------|
| 1 | 🇦🇷 Argentina | 1734 | Quartas (a disputar) |
| 2 | 🇫🇷 France | 1718 | ✅ Semifinal — 2×0 Morocco |
| 7 | 🏴󠁧󠁢󠁥󠁮󠁧󠁿 England | 1622 | Quartas (a disputar) |
| 9 | 🇪🇸 Spain | 1610 | Quartas (a disputar) |
| 10 | 🇧🇪 Belgium | 1607 | Quartas (a disputar) |
| 13 | 🇲🇦 Morocco | 1565 | ❌ Eliminada (QF) |
| 14 | 🇳🇴 Norway | 1560 | Quartas (a disputar) |
| 16 | 🇨🇭 Switzerland | 1547 | Quartas (a disputar) |

*ELO calculado sobre todos os 1.061 jogos de Copa do Mundo Masculina (1930–2026).*

---

## Pipeline em 3 etapas

### 1 · ELO Rating — quem é mais forte?

Calculamos um rating dinâmico para cada seleção a partir de **todos os resultados históricos** das Copas Masculinas (1930–2026), incluindo os 96 resultados reais da Copa 2026 já disputados.

O ELO funciona como o ranking de xadrez: vencer um adversário com rating alto vale mais do que vencer um adversário fraco. O rating é atualizado jogo a jogo, em ordem cronológica, capturando a força atual de cada seleção sem depender de rankings externos ou critérios subjetivos.

```
ratings[time_A] += K × (resultado - probabilidade_esperada)
                    ↑
              K = 30  (testamos outros valores — 30 equilibra
                        memória histórica e responsividade)
```

Seleções sem histórico recente partem do ELO base (1.500) e constroem reputação pelo desempenho. Isso disciplina o modelo: sem dados, sem confiança alta.

### 2 · XGBoost — o que vai acontecer neste jogo?

Com os ELOs calculados, treinamos um **classificador multi-classe** para prever o resultado de qualquer partida: vitória do mandante (0), empate (1) ou vitória do visitante (2).

```python
features = ["elo_home", "elo_away", "elo_diff"]  # apenas 3 variáveis
```

A restrição é intencional: feature engineering elaborada com 1.300 amostras aumenta variância sem reduzir viés. Três features simples + XGBoost com regularização moderada superam modelos mais complexos nas validações.

Comparamos com Regressão Logística como baseline para quantificar o ganho real de complexidade:

| Modelo | Acurácia | vs. baseline aleatório |
|--------|----------|------------------------|
| **XGBoost** | **58%** | **+75%** |
| Regressão Logística | ~55% | +67% |
| Chute aleatório (3 classes) | 33% | — |

XGBoost supera o baseline em acurácia **e** em log-loss — as probabilidades geradas são mais calibradas, o que importa diretamente para a qualidade da simulação Monte Carlo.

### 3 · Monte Carlo — e o torneio inteiro?

A chance de ser campeão não é a probabilidade de vencer um jogo. É a probabilidade de vencer **todos os jogos necessários**, contra adversários que também chegaram até ali.

Simulamos o torneio **10.000 vezes**:

```
Para cada simulação:
  1. Embaralha o bracket com as seleções vivas
  2. Para cada confronto: XGBoost gera P(vitória A), P(empate), P(vitória B)
  3. Sorteio ponderado determina o vencedor
  4. Avança para a próxima rodada até restar 1 seleção
  5. Registra qual seleção chegou a cada fase

Resultado: P(campeã) = contagem de títulos / 10.000
```

Com 10.000 amostras, o erro estatístico fica abaixo de 1 ponto percentual no nível de seleção. O custo computacional é < 1 segundo — o pipeline inteiro roda em < 5 segundos.

---

## Arquitetura

```
app.py                       # Entry point Streamlit
│
components/
├── data_loader.py           # Pipeline completo: load → ELO → train → simulate
│                            # Tudo cacheado (@st.cache_data / @st.cache_resource)
├── tab1_overview.py         # Hero card · confrontos da fase atual · ranking
├── tab2_team.py             # Team profile · funil de probabilidades por fase
├── tab3_why.py              # ELO ranking · histórico ELO · importância de features · H2H
├── tab4_trust.py            # Métricas do modelo · limitações · fontes de dados
├── teams_2026.py            # Lista canônica das 48 seleções classificadas
└── flags.py                 # Mapeamento seleção → emoji de bandeira
│
data/
├── fjelstul/matches.csv     # 964 jogos históricos — Copa Masculina 1930–2022
└── wc2026_matches.csv       # 96 jogos reais da Copa 2026 (atualizado conforme torneio avança)
```

O pipeline não usa banco de dados, arquivos serializados ou APIs externas. Tudo roda em memória a partir dos dois CSVs, o que simplifica o deploy e garante reprodutibilidade.

---

## Decisões técnicas

**Por que ELO e não o Ranking FIFA?**
O Ranking FIFA usa critérios proprietários com pesos não documentados e muda de metodologia entre edições. ELO é derivável a partir dos mesmos dados que o modelo usa, auditável e sem dependência externa.

**Por que XGBoost com 3 features e não uma rede neural?**
Com ~1.300 amostras, qualquer modelo com alta capacidade vai overfit. Testamos feature engineering adicional (margem de vitória, sequência de resultados recentes) — o ganho foi marginal e a variância aumentou. XGBoost com regularização supera redes neurais neste regime de dados.

**Por que Monte Carlo e não cálculo analítico das probabilidades?**
A probabilidade exata de ser campeão exigiria enumerar todos os caminhos possíveis no bracket — fatorialmente complexo. Monte Carlo com 10.000 amostras converge para erro < 1% em milissegundos.

**Por que não há decaimento temporal no ELO?**
Testamos um fator de decaimento que reduz o peso de jogos antigos. Nas validações retrospectivas (prever Copa N a partir das Copas 1 até N-1), o decaimento degradou a calibração. O intervalo de 4 anos entre Copas já funciona como filtro natural de obsolescência.

---

## Dados

| Fonte | Conteúdo | Volume |
|-------|----------|--------|
| [Fjelstul World Cup Database](https://github.com/jfjelstul/worldcup) | Copas Masculinas 1930–2022 | 964 jogos |
| Resultados oficiais FIFA 2026 | Copa em andamento — atualizado manualmente | 96 jogos |

A base Fjelstul foi filtrada para excluir as Copas Femininas (1991–2019). Incluir resultados femininos inflacionaria o ELO de seleções como EUA, Japão e Noruega, cujos programas masculinos têm histórico radicalmente diferente.

---

## Rodar localmente

```bash
git clone https://github.com/rodrigohigashi/World_Cup_2026_predictions
cd World_Cup_2026_predictions
pip install -r requirements.txt
streamlit run app.py
```

Sem configuração adicional. O pipeline detecta automaticamente as seleções vivas a partir dos resultados no CSV — adicionar um novo jogo ao `wc2026_matches.csv` atualiza todo o modelo.

---

## Limitações

Documentadas como parte da metodologia, não como rodapé de disclaimer:

- **ELO apenas de Copas do Mundo** — eliminatórias, Copa das Confederações e amistosos não entram. Seleções que raramente se classificam têm histórico limitado e ELO menos confiável.
- **Pênaltis como 50/50** — decisões por pênaltis são simuladas como sorteio. Há evidência de que alguns países têm vantagem estatística (e.g., Alemanha historicamente), mas o volume de dados por seleção é muito pequeno para modelar com confiança.
- **Bracket aleatório** — o chaveamento real do torneio é substituído por sorteio em cada simulação. Isso subestima o impacto de cruzamentos favoráveis ou desfavoráveis.
- **Split treino/teste aleatório** — um split temporal (treinar em Copas até 2014, testar em 2018 e 2022) seria metodologicamente mais rigoroso. Com ~1.300 amostras, o impacto prático é limitado.
- **Sem modelagem de forma recente** — o ELO captura força histórica acumulada. Um time em má fase no ano da Copa não tem esse sinal capturado.

---

## Stack

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat&logo=python&logoColor=white)
![XGBoost](https://img.shields.io/badge/XGBoost-2.0+-FF6600?style=flat)
![Streamlit](https://img.shields.io/badge/Streamlit-1.35+-FF4B4B?style=flat&logo=streamlit&logoColor=white)
![Plotly](https://img.shields.io/badge/Plotly-5.18+-3F4F75?style=flat&logo=plotly&logoColor=white)

---

*Projeto por [Rodrigo Higashi](https://github.com/rodrigohigashi) · Copa do Mundo 2026*

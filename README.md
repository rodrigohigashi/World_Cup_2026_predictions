# Copa do Mundo 2026 — Simulador com Machine Learning

Projeto de previsão de resultados da Copa do Mundo 2026 usando **ELO Rating**, **XGBoost** e **Simulação Monte Carlo**.

A ideia central: treinar um modelo com dados históricos de todas as Copas (1930–2022) e simular o torneio completo 10.000 vezes para estimar a probabilidade de cada seleção ser campeã.

---

## Demonstração rápida

```
PROBABILIDADE DE SER CAMPEÃO — Copa 2026 (simulação com dados históricos)
=============================================
   1. França          ████████████  19%
   2. Brasil          ████████      14%
   3. Alemanha        ███████       13%
   ...
=============================================
Baseado em 10.000 simulações Monte Carlo
```

---

## Como funciona

O projeto tem três camadas:

### 1. ELO Rating — medindo a força de cada seleção

Cada seleção começa com 1500 pontos. Após cada jogo da Copa, os pontos são atualizados com base no resultado **e na força do adversário**:

- Vencer um time forte → ganha muitos pontos
- Vencer um time fraco → ganha poucos pontos
- Perder para um fraco → perde muito

Isso é muito mais informativo do que uma simples taxa de vitórias, porque **considera a qualidade dos adversários**.

### 2. XGBoost — prevendo o resultado de um jogo

Com o ELO calculado, treinamos um classificador para prever o resultado de cada partida (vitória do mandante / empate / vitória do visitante) usando como features:

- ELO do time da casa
- ELO do time visitante
- Diferença entre os dois

**Desempenho no conjunto de teste:** 58% de acurácia (vs. 33% de um chute aleatório entre 3 classes).

### 3. Monte Carlo — simulando o torneio completo

O torneio tem um chaveamento em cascata: quem você enfrenta nas quartas depende do que aconteceu nos grupos e nas oitavas. Não existe fórmula fechada para calcular a probabilidade de ser campeão considerando todos os caminhos possíveis.

A solução: simular o torneio inteiro 10.000 vezes usando as probabilidades do modelo em cada jogo. O resultado é a frequência com que cada seleção foi campeã nessas simulações.

**Empates no mata-mata:** tratados como pênaltis (50/50), já que estatisticamente cobranças de pênalti são muito imprevisíveis.

---

## Estrutura do projeto

```
Copa do Mundo 2026/
├── copa2026.ipynb          # Notebook principal — metodologia completa e didática
├── src/
│   ├── download_data.py    # Download dos dados (Fjelstul + Kaggle)
│   ├── build_dataset.py    # Feature engineering
│   └── model.py            # Treino, avaliação e simulação Monte Carlo
├── data/
│   ├── fjelstul/           # Dados históricos 1930–2022 (baixados automaticamente)
│   ├── kaggle_2026/        # Resultados da Copa 2026 em andamento (pendente)
│   └── processed/          # Dataset processado e modelo treinado
└── requirements.txt
```

---

## Fontes de dados

| Fonte | O que contém | Status |
|-------|-------------|--------|
| [Fjelstul World Cup Database](https://github.com/jfjelstul/worldcup) | 1.248 jogos da Copa (1930–2022), gols, fases, estádios | ✅ Integrado |
| Kaggle FIFA World Cup 2026 | Elencos atuais + resultados em andamento | ⏳ Pendente |

---

## Como rodar

```bash
# 1. Instalar dependências
pip install -r requirements.txt

# 2. Baixar os dados históricos
python src/download_data.py

# 3. Abrir o notebook
jupyter lab copa2026.ipynb
```

O notebook `copa2026.ipynb` é o ponto de entrada principal — contém todos os passos com explicações em cada célula, do carregamento dos dados até os resultados finais da simulação.

---

## O que está planejado

### Dados
- [ ] Integrar resultados reais da Copa 2026 (Kaggle) para atualizar o ELO com a forma atual das seleções
- [ ] Usar o chaveamento real do torneio (em vez de simulação aleatória)
- [ ] Unificar West Germany → Germany e Yugoslavia → sucessores

### Modelo
- [ ] Adicionar features de eliminatórias e amistosos (não só Copa)
- [ ] Explorar calibração de probabilidades

### Produto
- [ ] Aplicativo Streamlit com 5 abas, seguindo o Princípio da Pirâmide (Minto):
  - **Favoritos** — "Quem tem mais chance de ganhar?"
  - **Por Seleção** — "Como está a situação da minha seleção?"
  - **Por que isso?** — "Por que o modelo chegou a essa conclusão?"
  - **Posso confiar?** — "Quão confiável é esse modelo?"
  - **E se...?** — "Como as chances mudariam em um cenário diferente?" *(v1 ou v2 — em avaliação)*

---

## Limitações conhecidas

- O ELO foi calculado **apenas com jogos de Copa do Mundo** — não inclui eliminatórias nem amistosos, o que subestima a força de seleções que raramente se classificam
- Pênaltis são tratados como 50/50, o que é uma simplificação consciente
- West Germany e Germany são tratados como times diferentes no dataset histórico
- O chaveamento nas simulações atuais é aleatório — será substituído pelo bracket real quando os dados do Kaggle forem integrados

---

## Tecnologias

- **Python 3.10**
- **pandas / numpy** — manipulação de dados
- **XGBoost** — modelo de classificação
- **scikit-learn** — avaliação e pré-processamento
- **matplotlib / seaborn** — visualizações
- **Jupyter Lab** — notebook interativo
- **Streamlit** — aplicativo web *(planejado)*

---

## Autor

Projeto desenvolvido como estudo aplicado de Machine Learning em dados de futebol.

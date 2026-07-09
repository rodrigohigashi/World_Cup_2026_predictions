import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from components.flags import EMOJI_FONT
from components.theme import (
    GOLD, BLUE, RED, T2, T3, apply_theme,
    section_header_html, caption_html, alert_html,
)


def _metrics_table(metrics: dict) -> pd.DataFrame:
    rows = []
    for model_name, m in metrics.items():
        rows.append({
            "Modelo":    model_name,
            "Acurácia":  f"{m['accuracy']:.1%}",
            "Log-loss":  f"{m['log_loss']:.3f}",
        })
    return pd.DataFrame(rows)


def _comparison_chart(metrics: dict) -> go.Figure:
    models   = list(metrics.keys())
    accs     = [metrics[m]["accuracy"] * 100 for m in models]
    baseline = 33.3

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=models, y=accs,
        text=[f"<b>{a:.1f}%</b>" for a in accs],
        textposition="outside",
        cliponaxis=False,
        textfont=dict(color=T2),
        marker_color=[GOLD, BLUE],
        hovertemplate="%{x}: <b>%{y:.1f}%</b><extra></extra>",
    ))
    fig.add_hline(
        y=baseline, line_dash="dash",
        line_color="rgba(239,68,68,0.55)",
        annotation_text=f"Chute aleatório ({baseline:.0f}%)",
        annotation_position="top right",
        annotation_font_color=RED,
    )
    fig.update_layout(
        height=260,
        margin=dict(l=10, r=10, t=10, b=10),
        yaxis=dict(range=[0, max(accs) * 1.3], title="Acurácia (%)"),
        xaxis=dict(showgrid=False),
        showlegend=False,
    )
    return apply_theme(fig)


def render(metrics: dict, n_simulacoes: int, matches: pd.DataFrame):
    m26      = matches[matches["match_date"] >= "2026-01-01"]
    n_jogos  = len(m26)
    data_max = m26["match_date"].max().strftime("%Y-%m-%d")

    st.markdown(
        section_header_html(
            "Posso confiar nesse modelo?",
            "Desempenho real do modelo, limitações e decisões metodológicas. Transparência é parte do projeto.",
        ),
        unsafe_allow_html=True,
    )

    st.markdown(
        f"<p style='font-size:.72rem;color:{T3};text-transform:uppercase;"
        f"letter-spacing:.12em;font-weight:700;margin:.5rem 0 .25rem'>"
        f"XGBoost vs. Regressão Logística</p>",
        unsafe_allow_html=True,
    )
    st.markdown(caption_html("Comparamos dois modelos para quantificar o ganho real de complexidade."), unsafe_allow_html=True)
    st.plotly_chart(_comparison_chart(metrics), width="stretch")
    st.dataframe(_metrics_table(metrics), hide_index=True, width="stretch")
    st.markdown(
        caption_html(
            f"<strong style='color:{T2}'>Acurácia</strong> = proporção de jogos com resultado previsto corretamente. "
            f"<strong style='color:{T2}'>Log-loss</strong> = calibração das probabilidades (menor = melhor)."
        ),
        unsafe_allow_html=True,
    )

    st.markdown("---")

    st.markdown(
        f"<p style='font-size:.72rem;color:{T3};text-transform:uppercase;"
        f"letter-spacing:.12em;font-weight:700;margin:.5rem 0 .5rem'>"
        f"Limitações que você deve saber</p>",
        unsafe_allow_html=True,
    )
    st.markdown(
        alert_html(
            f"<strong style='color:{T2}'>ELO calculado apenas com jogos de Copa do Mundo</strong><br>"
            "Seleções que raramente se classificam têm ELO subestimado, "
            "pois eliminatórias e amistosos não entram no cálculo."
        ),
        unsafe_allow_html=True,
    )
    with st.expander("Ver todas as limitações"):
        st.markdown("""
- **Pênaltis = 50/50** — Decisões por pênaltis são tratadas como sorteio.
- **Chaveamento aleatório** — O mata-mata é simulado com chaveamento aleatório em cada simulação.
- **Dados só de Copa** — O modelo vê apenas o comportamento das seleções em Copas do Mundo.
- **Empates no mata-mata** — Quando o modelo prevê empate numa fase eliminatória, simulamos pênaltis (50/50).
- **Sem forma recente** — O ELO captura força histórica acumulada; um time em má fase não tem esse sinal capturado.
        """)

    st.markdown("---")

    st.markdown(
        f"<p style='font-size:.72rem;color:{T3};text-transform:uppercase;"
        f"letter-spacing:.12em;font-weight:700;margin:.5rem 0 .5rem'>"
        f"Como funciona — resumo</p>",
        unsafe_allow_html=True,
    )
    st.markdown(f"""
| Etapa | O que faz |
|-------|-----------|
| **ELO Rating** | Calcula a força de cada seleção com todos os resultados históricos das Copas Masculinas (1930–2026) |
| **XGBoost** | Usa o ELO dos dois times para prever a probabilidade de vitória, empate ou derrota em cada jogo |
| **Monte Carlo** | Simula o torneio completo {n_simulacoes:,} vezes para estimar a chance de cada seleção ser campeã |
    """)

    st.markdown("---")

    st.markdown(
        f"<p style='font-size:.72rem;color:{T3};text-transform:uppercase;"
        f"letter-spacing:.12em;font-weight:700;margin:.5rem 0 .5rem'>"
        f"Fontes de dados</p>",
        unsafe_allow_html=True,
    )
    col1, col2 = st.columns(2)
    col1.markdown(
        "**Fjelstul World Cup Database**  \n"
        "1.248 jogos · Copa Masculina 1930–2022  \n"
        "[github.com/jfjelstul/worldcup](https://github.com/jfjelstul/worldcup)"
    )
    col2.markdown(
        "**Resultados Copa 2026**  \n"
        f"{n_jogos} jogos · Fase de grupos + Round of 32/16  \n"
        f"Cobertura parcial (atualizado em {data_max})"
    )

    st.markdown("---")
    st.markdown(
        "📓 [Ver notebook completo](https://github.com/rodrigohigashi/World_Cup_2026_predictions) · "
        "💻 [Código no GitHub](https://github.com/rodrigohigashi/World_Cup_2026_predictions)"
    )

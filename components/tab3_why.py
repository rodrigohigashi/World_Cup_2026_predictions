import plotly.graph_objects as go
import streamlit as st
import pandas as pd
import numpy as np
from components.flags import label, get_flag, get_flag_url, get_team_code, EMOJI_FONT
from components.data_loader import _prever_neutral
from components.theme import (
    BG1, BG2, BG3, GOLD, GREEN, BLUE, T1, T2, T3, BORDER,
    apply_theme, section_header_html, caption_html,
)

COLOR_BASE = BLUE
COLOR_OTHER = T3


def _elo_chart(ranking: pd.Series, highlight: str) -> go.Figure:
    top20  = ranking.head(20)
    colors = [GOLD if t == highlight else COLOR_BASE for t in top20.index]
    labels = [label(t) for t in top20.index]
    values = top20.values.round(0)

    fig = go.Figure(go.Bar(
        x=values[::-1],
        y=labels[::-1],
        orientation="h",
        marker_color=colors[::-1],
        text=[f"{v:.0f}" for v in values[::-1]],
        textposition="outside",
        cliponaxis=False,
        textfont=dict(color=T2),
        hovertemplate="<b>%{y}</b><br>ELO: %{x:.0f}<extra></extra>",
    ))
    fig.update_layout(
        height=max(340, 20 * 38),
        margin=dict(l=10, r=60, t=10, b=30),
        xaxis=dict(
            title="ELO Rating",
            range=[values.min() * 0.97, values.max() * 1.06],
        ),
        yaxis=dict(showgrid=False, tickfont=dict(size=13)),
        showlegend=False,
    )
    return apply_theme(fig)


def _elo_history_chart(matches: pd.DataFrame, team: str) -> go.Figure:
    jogos = matches[
        (matches["home_team_name"] == team) | (matches["away_team_name"] == team)
    ].copy()
    jogos["elo_team"] = jogos.apply(
        lambda r: r["elo_home"] if r["home_team_name"] == team else r["elo_away"], axis=1
    )

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=jogos["match_date"], y=jogos["elo_team"],
        mode="lines", line=dict(width=2, color=GOLD),
        fill="tozeroy", fillcolor="rgba(201,162,39,0.07)",
        hovertemplate="%{x|%Y}: ELO %{y:.0f}<extra></extra>",
        name=team,
    ))
    fig.add_hline(
        y=1500, line_dash="dash",
        line_color="rgba(123,159,190,0.3)",
        annotation_text="ELO médio (1500)",
        annotation_font_color=T3,
    )
    fig.update_layout(
        height=260,
        margin=dict(l=10, r=10, t=10, b=30),
        yaxis=dict(title="ELO"),
        xaxis=dict(title="Ano", showgrid=False),
        showlegend=False,
    )
    return apply_theme(fig)


def _h2h_html(team_a: str, team_b: str, model, elo_a: float, elo_b: float) -> str:
    _pw, _pd, _pa = _prever_neutral(model, elo_a, elo_b)
    pw  = _pw  * 100
    pd_ = _pd  * 100
    pa  = _pa  * 100
    url_a = get_flag_url(team_a)
    url_b = get_flag_url(team_b)
    code_a = get_team_code(team_a)
    code_b = get_team_code(team_b)
    img_a = f'<img src="{url_a}" style="width:56px;height:auto;display:block">' if url_a else code_a
    img_b = f'<img src="{url_b}" style="width:56px;height:auto;display:block">' if url_b else code_b

    def bar_row(pct, color, row_label):
        return f"""
<div style="display:flex;align-items:center;gap:.75rem">
  <div style="width:3.5rem;text-align:right;font-size:.88rem;font-weight:800;
    color:{color};font-variant-numeric:tabular-nums">{pct:.1f}%</div>
  <div style="flex:1;height:7px;background:{BG3};border-radius:999px;overflow:hidden">
    <div style="width:{pct:.1f}%;height:100%;border-radius:999px;background:{color}"></div>
  </div>
  <div style="width:4rem;font-size:.68rem;font-weight:600;color:{T3}">{row_label}</div>
</div>
"""

    return f"""
<div style="background:{BG1};border:1px solid {BORDER};border-radius:14px;padding:1.5rem">
  <div style="display:grid;grid-template-columns:1fr auto 1fr;
    align-items:center;gap:1rem;margin-bottom:1.25rem">
    <div>
      <div style="margin-bottom:.4rem">{img_a}</div>
      <div style="font-size:.95rem;font-weight:800;color:{T1}">{team_a}</div>
      <div style="font-size:.7rem;color:{T3};font-variant-numeric:tabular-nums">ELO {elo_a:.0f}</div>
    </div>
    <div style="text-align:center">
      <div style="font-size:.58rem;font-weight:800;letter-spacing:.15em;
        text-transform:uppercase;color:{T3}">vs</div>
    </div>
    <div style="text-align:right">
      <div style="margin-bottom:.4rem;display:flex;justify-content:flex-end">{img_b}</div>
      <div style="font-size:.95rem;font-weight:800;color:{T1}">{team_b}</div>
      <div style="font-size:.7rem;color:{T3};font-variant-numeric:tabular-nums">ELO {elo_b:.0f}</div>
    </div>
  </div>
  <div style="height:1px;background:{BORDER};margin-bottom:1rem"></div>
  <div style="display:flex;flex-direction:column;gap:.7rem">
    {bar_row(pw,  GOLD,     f"Vitória {code_a}")}
    {bar_row(pd_, T3,       "Empate")}
    {bar_row(pa,  BLUE,     f"Vitória {code_b}")}
  </div>
  <p style="font-size:.68rem;color:{T3};margin-top:1rem;text-align:center;margin-bottom:0">
    {team_a} (mandante) vs {team_b} &nbsp;·&nbsp; probabilidades baseadas nos ELOs atuais
  </p>
</div>
"""


def _feature_importance_chart(model) -> go.Figure:
    importances = model.feature_importances_
    features    = ["ELO do mandante", "ELO do visitante", "Diferença de ELO"]
    order       = np.argsort(importances)

    fig = go.Figure(go.Bar(
        x=importances[order],
        y=[features[i] for i in order],
        orientation="h",
        marker_color=GOLD,
        text=[f"{v:.1%}" for v in importances[order]],
        textposition="outside",
        cliponaxis=False,
        textfont=dict(color=T2),
        hovertemplate="<b>%{y}</b><br>Importância: %{x:.1%}<extra></extra>",
    ))
    fig.update_layout(
        height=200,
        margin=dict(l=10, r=70, t=10, b=20),
        xaxis=dict(title="Importância relativa"),
        yaxis=dict(showgrid=False),
        showlegend=False,
    )
    return apply_theme(fig)


def render(prob_campea: pd.Series, matches: pd.DataFrame,
           elo_ratings: dict, ranking: pd.Series, xgb_model):

    st.markdown(section_header_html("Por que o modelo chegou a essa conclusão?"), unsafe_allow_html=True)

    teams = ranking.index.tolist()
    team  = st.selectbox("Selecione uma seleção", options=teams,
                         format_func=lambda t: f"{get_team_code(t)}  —  {t}", key="tab3_team")
    elo   = elo_ratings.get(team, 1500)

    flag_img = f'<img src="{get_flag_url(team)}" style="width:18px;height:auto;vertical-align:middle;margin-right:.35rem">' if get_flag_url(team) else ""
    st.markdown(
        f"<p style='font-size:.72rem;color:{T3};text-transform:uppercase;"
        f"letter-spacing:.12em;font-weight:700;margin:.5rem 0 .25rem'>"
        f"Ranking ELO — onde {flag_img}{team} está?</p>",
        unsafe_allow_html=True,
    )
    st.markdown(caption_html("Barra dourada = seleção selecionada. ELO mede força histórica em Copas."), unsafe_allow_html=True)
    st.plotly_chart(_elo_chart(ranking, team), width="stretch")

    st.markdown(
        f"<p style='font-size:.72rem;color:{T3};text-transform:uppercase;"
        f"letter-spacing:.12em;font-weight:700;margin:.5rem 0 .25rem'>"
        f"Evolução do ELO de {team}</p>",
        unsafe_allow_html=True,
    )
    st.plotly_chart(_elo_history_chart(matches, team), width="stretch")

    st.markdown(
        f"<p style='font-size:.72rem;color:{T3};text-transform:uppercase;"
        f"letter-spacing:.12em;font-weight:700;margin:.5rem 0 .25rem'>"
        f"O que o modelo considera mais importante?</p>",
        unsafe_allow_html=True,
    )
    st.markdown(caption_html("Importância de cada variável para a decisão do XGBoost."), unsafe_allow_html=True)
    st.plotly_chart(_feature_importance_chart(xgb_model), width="stretch")

    st.markdown(
        f"<p style='font-size:.72rem;color:{T3};text-transform:uppercase;"
        f"letter-spacing:.12em;font-weight:700;margin:1rem 0 .6rem'>"
        f"Confronto direto</p>",
        unsafe_allow_html=True,
    )
    opponents = [t for t in teams if t != team]
    opp       = st.selectbox("Adversário", options=opponents,
                             format_func=lambda t: f"{get_team_code(t)}  —  {t}", key="tab3_opp")
    elo_opp   = elo_ratings.get(opp, 1500)
    st.markdown(_h2h_html(team, opp, xgb_model, elo, elo_opp), unsafe_allow_html=True)

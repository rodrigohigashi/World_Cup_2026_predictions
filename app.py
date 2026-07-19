import streamlit as st
from components.data_loader import (
    load_matches, compute_elo, train_models, run_simulation, _alive_teams,
    get_current_stage_matches,
)
from components import tab1_overview, tab2_team, tab3_why, tab4_trust
from components.teams_2026 import TEAMS_2026
from components.theme import BG1, BORDER, GOLD, GREEN, T1, T2, T3

st.set_page_config(
    page_title="Copa do Mundo 2026 — Simulador",
    page_icon="🏆",
    layout="wide",
)

# ── Carrega dados ─────────────────────────────────────────────────────────────

with st.spinner("Carregando dados e rodando simulações..."):
    matches_raw       = load_matches()
    matches, elo_ratings, ranking = compute_elo(matches_raw)
    xgb_model, lr_model, metrics, X_test, y_test = train_models(matches)
    prob_campea, phase_probs = run_simulation(
        xgb_model, elo_ratings, ranking, matches, n=10_000
    )
    matchups    = get_current_stage_matches(matches_raw, elo_ratings, xgb_model)
    n_historico = int((matches_raw["match_date"] < "2026-01-01").sum())

# Contexto do torneio
m26           = matches_raw[matches_raw["match_date"] >= "2026-01-01"]
n_jogos_2026  = len(m26)
_m26_played   = m26[m26["result"] != "scheduled"]
data_max      = _m26_played["match_date"].max().strftime("%Y-%m-%d") if len(_m26_played) > 0 else "–"
_alive_set    = _alive_teams(matches_raw) & set(TEAMS_2026)
n_alive       = len(_alive_set)

if n_alive > 8:
    phase_name = "Round of 16"
elif n_alive > 4:
    phase_name = "Quartas de Final"
elif n_alive > 2:
    phase_name = "Semifinal"
elif n_alive > 1:
    phase_name = "Final"
else:
    phase_name = "Encerrada"

ranking_2026 = ranking[ranking.index.isin(TEAMS_2026)]

# Times eliminados nas QF em diante — aparecem no ranking com marcador de eliminação
_late_ko = m26[m26["stage_name"].isin(["quarter-final", "semi-final", "final"])]
_elim_late = (
    set(_late_ko.loc[_late_ko["result"] == "away team win", "home_team_name"]) |
    set(_late_ko.loc[_late_ko["result"] == "home team win", "away_team_name"])
) & set(TEAMS_2026)
eliminated_qf = sorted(_elim_late, key=lambda t: elo_ratings.get(t, 0), reverse=True)

# Terceiro lugar e finalista — destaque visual no ranking
def _ko_result_info(stage_df):
    played = stage_df[stage_df["result"] != "scheduled"]
    if played.empty:
        return None, None
    r = played.iloc[0]
    if r["result"] == "home team win":
        winner, loser = r["home_team_name"], r["away_team_name"]
        score_w = f"{int(r['home_team_score'])}×{int(r['away_team_score'])}"
        score_l = f"{int(r['away_team_score'])}×{int(r['home_team_score'])}"
    else:
        winner, loser = r["away_team_name"], r["home_team_name"]
        score_w = f"{int(r['away_team_score'])}×{int(r['home_team_score'])}"
        score_l = f"{int(r['home_team_score'])}×{int(r['away_team_score'])}"
    return (
        {"team": winner, "score": score_w, "opponent": loser},
        {"team": loser,  "score": score_l, "opponent": winner},
    )

_tp_winner, _       = _ko_result_info(m26[m26["stage_name"] == "third-place match"])
_fn_winner, _fn_loser = _ko_result_info(m26[m26["stage_name"] == "final"])
third_place_info = _tp_winner  # ganhador do 3º lugar
runner_up_info   = _fn_loser   # perdedor da final = vice
champion_info    = _fn_winner  # {"team","score","opponent"} ou None

# ── Cabeçalho ────────────────────────────────────────────────────────────────

# Barra de contexto ao vivo
st.markdown(f"""
<div style="
  display:flex;align-items:center;gap:1.5rem;flex-wrap:wrap;
  background:{BG1};border:1px solid {BORDER};
  border-radius:10px;padding:.85rem 1.25rem;margin-bottom:1.25rem;
">
  <div style="display:flex;align-items:center;gap:.45rem">
    <span style="width:7px;height:7px;border-radius:50%;background:{GREEN};display:inline-block;flex-shrink:0"></span>
    <span style="font-size:.62rem;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:{T3}">Ao vivo</span>
  </div>
  <div style="width:1px;height:1.5rem;background:{BORDER}"></div>
  <div>
    <div style="font-size:1.1rem;font-weight:800;color:{T1};line-height:1;font-variant-numeric:tabular-nums">{n_alive}</div>
    <div style="font-size:.6rem;font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:{T3};margin-top:.15rem">seleções vivas</div>
  </div>
  <div style="width:1px;height:1.5rem;background:{BORDER}"></div>
  <div>
    <div style="font-size:1rem;font-weight:800;color:{T1};line-height:1">{phase_name}</div>
    <div style="font-size:.6rem;font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:{T3};margin-top:.15rem">fase atual</div>
  </div>
  <div style="width:1px;height:1.5rem;background:{BORDER}"></div>
  <div>
    <div style="font-size:1.1rem;font-weight:800;color:{T1};line-height:1;font-variant-numeric:tabular-nums">{n_jogos_2026}</div>
    <div style="font-size:.6rem;font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:{T3};margin-top:.15rem">jogos 2026</div>
  </div>
  <div style="width:1px;height:1.5rem;background:{BORDER}"></div>
  <div style="margin-left:auto">
    <div style="font-size:.88rem;font-weight:700;color:{T2};font-variant-numeric:tabular-nums">{data_max}</div>
    <div style="font-size:.6rem;font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:{T3};margin-top:.15rem">última atualização</div>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Abas ─────────────────────────────────────────────────────────────────────

tabs = st.tabs([
    "🥇 Quem vai ganhar?",
    "🔍 Minha seleção",
    "🤔 Por que isso?",
    "📊 Posso confiar?",
])

with tabs[0]:
    tab1_overview.render(
        prob_campea, phase_probs,
        n_simulacoes=10_000,
        n_alive=n_alive,
        phase_name=phase_name,
        data_max=data_max,
        matchups=matchups,
        n_historico=n_historico,
        eliminated_qf=eliminated_qf,
        third_place_info=third_place_info,
        runner_up_info=runner_up_info,
        champion_info=champion_info,
    )

with tabs[1]:
    tab2_team.render(prob_campea, phase_probs, elo_ratings, ranking_2026)

with tabs[2]:
    tab3_why.render(prob_campea, matches, elo_ratings, ranking_2026, xgb_model)

with tabs[3]:
    tab4_trust.render(metrics, n_simulacoes=10_000, matches=matches)

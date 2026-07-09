import streamlit as st
import pandas as pd
from components.flags import label, get_flag, get_flag_url, get_nation_color, get_team_code
from components.theme import (
    BG1, BG2, BG3, GOLD, GREEN, RED, BLUE, T1, T2, T3, BORDER,
)


def _hex_to_rgba(hex_color: str, alpha: float) -> str:
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"


# ── Team profile header ───────────────────────────────────────────────────────

def _team_header_html(team: str, elo: float, rank, prob: float,
                      prob_rank, alive: bool,
                      elo_max: float, elo_min: float, n_total: int) -> str:
    flag_url   = get_flag_url(team)
    flag_emoji = get_flag(team)
    nc         = get_nation_color(team)
    code       = get_team_code(team)

    wash_hi   = _hex_to_rgba(nc, 0.20)
    wash_lo   = _hex_to_rgba(nc, 0.05)
    nc_border = _hex_to_rgba(nc, 0.30)
    nc_bg     = _hex_to_rgba(nc, 0.12)
    nc_bd     = _hex_to_rgba(nc, 0.20)
    nc_bar    = _hex_to_rgba(nc, 0.65)

    if flag_url:
        flag_el = (
            f'<img src="{flag_url}" alt="{team}" '
            f'style="width:90px;height:auto;border-radius:7px;display:block;'
            f'box-shadow:0 8px 24px rgba(0,0,0,.55);'
            f'border:1px solid rgba(255,255,255,.1)">'
        )
    else:
        flag_el = f'<div style="font-size:4rem;line-height:1">{flag_emoji}</div>'

    if alive:
        status_badge = (
            f'<span style="display:inline-flex;align-items:center;gap:.3rem;'
            f'padding:.2rem .6rem;border-radius:999px;'
            f'background:rgba(34,197,94,.12);border:1px solid rgba(34,197,94,.25);'
            f'font-size:.56rem;font-weight:800;letter-spacing:.08em;'
            f'text-transform:uppercase;color:{GREEN}">'
            f'<span style="width:5px;height:5px;border-radius:50%;'
            f'background:{GREEN};display:inline-block;flex-shrink:0"></span>'
            f'Ativa</span>'
        )
    else:
        status_badge = (
            f'<span style="display:inline-flex;align-items:center;gap:.3rem;'
            f'padding:.2rem .6rem;border-radius:999px;'
            f'background:rgba(239,68,68,.12);border:1px solid rgba(239,68,68,.25);'
            f'font-size:.56rem;font-weight:800;letter-spacing:.08em;'
            f'text-transform:uppercase;color:{RED}">'
            f'Eliminada</span>'
        )

    elo_range = max(elo_max - elo_min, 1)
    elo_pct   = max(0, min(100, (elo - elo_min) / elo_range * 100))

    prob_rank_badge = ""
    if prob_rank:
        prob_rank_badge = (
            f'<span style="display:inline-flex;align-items:center;'
            f'padding:.2rem .6rem;border-radius:999px;'
            f'background:rgba(201,162,39,.12);border:1px solid rgba(201,162,39,.22);'
            f'font-size:.56rem;font-weight:800;letter-spacing:.08em;'
            f'text-transform:uppercase;color:{GOLD}">'
            f'Favorita #{prob_rank}</span>'
        )

    stat_badge = (
        f'<span style="display:inline-flex;align-items:center;'
        f'padding:.2rem .6rem;border-radius:999px;'
        f'background:rgba(123,159,190,.1);border:1px solid rgba(123,159,190,.18);'
        f'font-size:.56rem;font-weight:800;letter-spacing:.08em;'
        f'text-transform:uppercase;color:{T2}">'
    )

    return (
        f'<div style="position:relative;overflow:hidden;border-radius:14px;'
        f'background:linear-gradient(165deg,#071529 0%,#0B1E3A 60%,#060F1C 100%);'
        f'border:1px solid {nc_border};margin-bottom:1.5rem">'

        f'<div style="height:3px;background:{nc}"></div>'

        f'<div style="position:absolute;top:0;left:0;right:0;bottom:0;pointer-events:none;'
        f'background:linear-gradient(135deg,{wash_hi} 0%,{wash_lo} 45%,transparent 70%)"></div>'

        f'<div style="position:relative;padding:1.75rem 2rem;'
        f'display:grid;grid-template-columns:auto 1fr;gap:1.75rem;align-items:center">'

        f'<div style="flex-shrink:0">{flag_el}</div>'

        f'<div>'

        f'<div style="display:flex;align-items:center;gap:.7rem;flex-wrap:wrap;margin-bottom:.7rem">'
        f'<span style="font-size:1.9rem;font-weight:900;letter-spacing:-.03em;'
        f'color:{T1};line-height:1">{team}</span>'
        f'<span style="font-size:.65rem;font-weight:900;letter-spacing:.14em;'
        f'text-transform:uppercase;color:{nc};'
        f'background:{nc_bg};border:1px solid {nc_bd};'
        f'border-radius:4px;padding:.15rem .45rem">{code}</span>'
        f'</div>'

        f'<div style="display:flex;align-items:center;gap:.45rem;flex-wrap:wrap;margin-bottom:1.1rem">'
        f'{status_badge}'
        f'{stat_badge}ELO {elo:.0f}</span>'
        f'{stat_badge}#{rank} no ranking</span>'
        f'{prob_rank_badge}'
        f'</div>'

        f'<div>'
        f'<div style="display:flex;justify-content:space-between;margin-bottom:.3rem">'
        f'<span style="font-size:.54rem;font-weight:700;letter-spacing:.08em;'
        f'text-transform:uppercase;color:{T3}">'
        f'For&ccedil;a relativa &middot; {n_total} sele&ccedil;&otilde;es</span>'
        f'<span style="font-size:.54rem;color:{T3};font-variant-numeric:tabular-nums">'
        f'{elo:.0f} ELO</span>'
        f'</div>'
        f'<div style="height:5px;background:{BG3};border-radius:999px;overflow:hidden">'
        f'<div style="width:{elo_pct:.1f}%;height:100%;border-radius:999px;'
        f'background:linear-gradient(90deg,{nc},{nc_bar})"></div>'
        f'</div>'
        f'</div>'

        f'</div>'
        f'</div>'
        f'</div>'
    )


# ── Jornada no torneio ────────────────────────────────────────────────────────

def _journey_html(team: str, phase_probs: pd.DataFrame) -> str:
    nc       = get_nation_color(team)
    nc_bar   = _hex_to_rgba(nc, 0.60)
    flag_url   = get_flag_url(team)
    flag_emoji = get_flag(team)

    if team not in phase_probs.index:
        if flag_url:
            flag_el = (
                f'<img src="{flag_url}" alt="{team}" '
                f'style="width:55px;height:auto;border-radius:5px;'
                f'display:block;margin:0 auto .75rem;opacity:.45">'
            )
        else:
            flag_el = (
                f'<div style="font-size:2.5rem;opacity:.45;'
                f'text-align:center;margin-bottom:.5rem">{flag_emoji}</div>'
            )
        return (
            f'<div style="background:{BG1};border:1px solid rgba(239,68,68,.15);'
            f'border-left:3px solid {RED};border-radius:12px;'
            f'padding:2rem;text-align:center">'
            f'{flag_el}'
            f'<p style="color:{T3};font-size:.85rem;margin:0;line-height:1.55">'
            f'Sele&ccedil;&atilde;o eliminada &mdash; n&atilde;o inclu&iacute;da '
            f'na simula&ccedil;&atilde;o do mata-mata.'
            f'</p>'
            f'</div>'
        )

    row    = phase_probs.loc[team]
    phases = [
        ("Quartas",       "quartas", row.get("quartas", 0)),
        ("Semifinal",     "semi",    row.get("semi",    0)),
        ("Final",         "final",   row.get("final",   0)),
        ("T&iacute;tulo", "campeao", row.get("campeao", 0)),
    ]

    cards = ""
    for ph_label, _key, val in phases:
        pct       = val * 100
        is_title  = _key == "campeao"
        top_color = GOLD if is_title else nc
        num_color = GOLD if is_title else T1
        num_size  = "2rem" if is_title else "1.7rem"
        bar_fill  = (
            f"linear-gradient(90deg,{GOLD},#FFE580)"
            if is_title else
            f"linear-gradient(90deg,{nc},{nc_bar})"
        )

        cards += (
            f'<div style="background:{BG2};border:1px solid {BORDER};'
            f'border-top:2px solid {top_color};border-radius:10px;'
            f'padding:1.1rem .8rem .9rem;text-align:center;flex:1;min-width:0">'
            f'<div style="font-size:.54rem;font-weight:800;letter-spacing:.1em;'
            f'text-transform:uppercase;color:{T3};margin-bottom:.5rem">{ph_label}</div>'
            f'<div style="font-size:{num_size};font-weight:900;letter-spacing:-.04em;'
            f'color:{num_color};font-variant-numeric:tabular-nums;line-height:1">'
            f'{pct:.1f}'
            f'<span style="font-size:.85rem;opacity:.55">%</span>'
            f'</div>'
            f'<div style="height:3px;background:{BG3};border-radius:999px;'
            f'overflow:hidden;margin-top:.75rem">'
            f'<div style="width:{pct:.1f}%;height:100%;border-radius:999px;'
            f'background:{bar_fill}"></div>'
            f'</div>'
            f'</div>'
        )

    return f'<div style="display:flex;gap:.6rem">{cards}</div>'


# ── render ────────────────────────────────────────────────────────────────────

def render(prob_campea: pd.Series, phase_probs: pd.DataFrame,
           elo_ratings: dict, ranking: pd.Series):

    st.markdown(
        f"<style>"
        f"div[data-testid='stSelectbox'] label{{"
        f"font-size:.62rem !important;font-weight:700 !important;"
        f"letter-spacing:.12em !important;text-transform:uppercase !important;"
        f"color:{T3} !important}}"
        f"</style>",
        unsafe_allow_html=True,
    )

    teams_sorted = ranking.index.tolist()
    team = st.selectbox(
        "Seleção",
        options=teams_sorted,
        format_func=lambda t: f"{get_team_code(t)}  —  {t}",
    )

    elo       = elo_ratings.get(team, 1500)
    rank      = teams_sorted.index(team) + 1 if team in teams_sorted else "–"
    prob      = prob_campea.get(team, 0) * 100
    alive     = team in phase_probs.index
    elo_max   = float(ranking.max())
    elo_min   = float(ranking.min())
    n_total   = len(ranking)

    prob_list = list(prob_campea.index)
    prob_rank = prob_list.index(team) + 1 if team in prob_list else None

    st.markdown(
        _team_header_html(team, elo, rank, prob, prob_rank,
                          alive, elo_max, elo_min, n_total),
        unsafe_allow_html=True,
    )

    st.markdown(
        f'<div style="display:flex;align-items:center;gap:.75rem;margin-bottom:.7rem">'
        f'<span style="font-size:.6rem;font-weight:800;letter-spacing:.18em;'
        f'text-transform:uppercase;color:{T3}">Jornada no Torneio</span>'
        f'<div style="flex:1;height:1px;background:{BORDER}"></div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    st.markdown(_journey_html(team, phase_probs), unsafe_allow_html=True)

    st.markdown(
        f'<p style="margin:.6rem 0 0;font-size:.68rem;color:{T3};line-height:1.5">'
        f'Probabilidade de avan&ccedil;ar em cada fase &mdash; baseada em 10.000 '
        f'simula&ccedil;&otilde;es com {len(phase_probs)} sele&ccedil;&otilde;es no bracket.'
        f'</p>',
        unsafe_allow_html=True,
    )

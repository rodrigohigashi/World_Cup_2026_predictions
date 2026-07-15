import streamlit as st
import pandas as pd
from components.flags import label, get_flag, get_flag_url, get_nation_color, get_team_code
from components.theme import (
    BG1, BG2, BG3, GOLD, GREEN, BLUE, T1, T2, T3, BORDER, pill_html,
)


def _hex_to_rgba(hex_color: str, alpha: float) -> str:
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"


# ── 1. Faixa de progresso do torneio ─────────────────────────────────────────

def _progress_strip_html(phase_name: str) -> str:
    _STAGES    = ["Grupos", "Oitavas", "Quartas", "Semifinal", "Final"]
    _PHASE_IDX = {
        "Round of 16":      1,
        "Quartas de Final": 2,
        "Semifinal":        3,
        "Final":            4,
        "Encerrada":        5,
    }
    current = _PHASE_IDX.get(phase_name, 2)

    parts = ""
    for i, stage in enumerate(_STAGES):
        is_done    = i < current
        is_current = i == current

        if is_done:
            dot_style    = f"background:{GREEN};border:1.5px solid {GREEN}"
            inner        = (
                f'<svg width="8" height="8" viewBox="0 0 8 8" fill="none">'
                f'<path d="M1.5 4L3 5.5L6.5 2" stroke="white" '
                f'stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>'
                f'</svg>'
            )
            label_color  = T2
            label_weight = "700"
            label_size   = ".54rem"
        elif is_current:
            dot_style    = f"background:transparent;border:2px solid {GOLD}"
            inner        = (
                f'<div style="width:6px;height:6px;border-radius:50%;'
                f'background:{GOLD}"></div>'
            )
            label_color  = GOLD
            label_weight = "800"
            label_size   = ".58rem"
        else:
            dot_style    = f"background:transparent;border:1.5px solid {T3}"
            inner        = ""
            label_color  = T3
            label_weight = "600"
            label_size   = ".54rem"

        parts += (
            f'<div style="display:flex;flex-direction:column;align-items:center;'
            f'gap:.35rem;flex-shrink:0">'
            f'<div style="width:16px;height:16px;border-radius:50%;{dot_style};'
            f'display:flex;align-items:center;justify-content:center">'
            f'{inner}'
            f'</div>'
            f'<span style="font-size:{label_size};font-weight:{label_weight};'
            f'letter-spacing:.08em;text-transform:uppercase;color:{label_color};'
            f'white-space:nowrap">{stage}</span>'
            f'</div>'
        )

        if i < len(_STAGES) - 1:
            conn_color   = GREEN if i < current else T3
            conn_opacity = ".4"  if i < current else ".18"
            parts += (
                f'<div style="flex:1;height:1px;background:{conn_color};'
                f'opacity:{conn_opacity};align-self:flex-start;'
                f'margin-top:8px;min-width:.5rem"></div>'
            )

    return (
        f'<div style="background:{BG1};border:1px solid {BORDER};border-radius:10px;'
        f'padding:.85rem 2rem .8rem;margin-bottom:.75rem;'
        f'display:flex;align-items:flex-start">'
        + parts +
        f'</div>'
    )


# ── 2. Snapshot editorial ─────────────────────────────────────────────────────

def _snapshot_html(n_alive: int, top1_team: str, top1_prob: float) -> str:
    if top1_prob < 20:
        tension = (
            f"nenhuma sele&ccedil;&atilde;o passou de 20% &mdash; "
            f"o torneio nunca esteve t&atilde;o em aberto"
        )
    elif top1_prob < 30:
        tension = (
            f"mas com a probabilidade distribu&iacute;da, "
            f"nenhum favorito &eacute; absoluto"
        )
    else:
        tension = "e segura uma vantagem clara sobre o restante do campo"

    prob_text = f"{top1_prob:.1f}".replace(".", ",")

    return (
        f'<div style="padding:.65rem 1.25rem;margin-bottom:1.1rem;'
        f'border-left:2px solid {GOLD};background:rgba(201,162,39,.04);'
        f'border-radius:0 8px 8px 0">'
        f'<p style="margin:0;font-size:.82rem;color:{T2};line-height:1.6">'
        f'Restam <strong style="color:{T1}">{n_alive} sele&ccedil;&otilde;es</strong>'
        f' na disputa. '
        f'<strong style="color:{T1}">{top1_team}</strong> lidera as simula&ccedil;&otilde;es'
        f' com <strong style="color:{GOLD}">{prob_text}%</strong>'
        f' &mdash; {tension}.'
        f'</p>'
        f'</div>'
    )


# ── Hero ──────────────────────────────────────────────────────────────────────

def _hero_html(team: str, prob: float, n: int,
               n_alive: int, phase_name: str, data_max: str,
               runners: list, n_historico: int = 0) -> str:
    flag_url   = get_flag_url(team)
    flag_emoji = get_flag(team)
    if flag_url:
        flag_el = (
            f'<img src="{flag_url}" alt="{team}" '
            f'style="width:110px;height:auto;border-radius:7px;display:block;'
            f'box-shadow:0 8px 28px rgba(0,0,0,.55);'
            f'border:1px solid rgba(255,255,255,.09);margin-bottom:1.2rem">'
        )
    else:
        flag_el = (
            f'<div style="font-size:5rem;line-height:1;margin-bottom:1rem">'
            f'{flag_emoji}</div>'
        )

    nc      = get_nation_color(team)
    wash_hi = _hex_to_rgba(nc, 0.22)
    wash_lo = _hex_to_rgba(nc, 0.05)

    runner_pills = ""
    for r_team, r_prob in runners:
        r_url   = get_flag_url(r_team)
        r_emoji = get_flag(r_team)
        if r_url:
            r_img = (
                f'<img src="{r_url}" alt="{r_team}" '
                f'style="width:20px;height:13px;object-fit:cover;'
                f'border-radius:2px;flex-shrink:0">'
            )
        else:
            r_img = f'<span style="font-size:.9rem">{r_emoji}</span>'
        runner_pills += (
            f'<div style="display:inline-flex;align-items:center;gap:.4rem;'
            f'padding:.3rem .65rem;background:rgba(255,255,255,.04);'
            f'border:1px solid rgba(123,159,190,.1);border-radius:6px">'
            f'{r_img}'
            f'<span style="font-size:.68rem;font-weight:700;color:{T2}">{r_team}</span>'
            f'<span style="font-size:.7rem;font-weight:800;color:{T1};'
            f'font-variant-numeric:tabular-nums">{r_prob:.1f}%</span>'
            f'</div>'
        )

    num_span = (
        f'<span style="font-size:clamp(4rem,9vw,7.5rem);font-weight:900;letter-spacing:-.06em;'
        f'background:linear-gradient(175deg,#FFE580 0%,{GOLD} 45%,#7A5200 100%);'
        f'-webkit-background-clip:text;-webkit-text-fill-color:transparent;'
        f'background-clip:text;font-variant-numeric:tabular-nums">{prob:.1f}</span>'
        f'<span style="font-size:clamp(1.8rem,3.5vw,3rem);font-weight:900;'
        f'background:linear-gradient(175deg,#FFE580 0%,{GOLD} 45%,#7A5200 100%);'
        f'-webkit-background-clip:text;-webkit-text-fill-color:transparent;'
        f'background-clip:text">%</span>'
    )

    return (
        f'<div style="position:relative;overflow:hidden;border-radius:16px;margin-bottom:1.5rem;'
        f'background:linear-gradient(165deg,#071529 0%,#0B1E3A 60%,#060F1C 100%);'
        f'border:1px solid rgba(201,162,39,.18)">'

        f'<div style="height:3px;background:{nc};opacity:.75"></div>'

        f'<div style="position:absolute;inset:0;pointer-events:none;'
        f'background:repeating-linear-gradient(0deg,transparent,transparent 3px,'
        f'rgba(0,0,0,.04) 3px,rgba(0,0,0,.04) 4px)"></div>'

        f'<div style="position:absolute;bottom:-30px;left:50%;transform:translateX(-50%);'
        f'width:150%;height:180px;border-radius:50% 50% 0 0/80px 80px 0 0;'
        f'background:rgba(255,255,255,.012);border-top:1px solid rgba(255,255,255,.03);'
        f'pointer-events:none"></div>'

        f'<div style="position:absolute;top:16px;left:16px;width:16px;height:16px;'
        f'border-top:2px solid rgba(201,162,39,.55);border-left:2px solid rgba(201,162,39,.55)"></div>'
        f'<div style="position:absolute;top:16px;right:16px;width:16px;height:16px;'
        f'border-top:2px solid rgba(201,162,39,.55);border-right:2px solid rgba(201,162,39,.55)"></div>'
        f'<div style="position:absolute;bottom:36px;left:16px;width:16px;height:16px;'
        f'border-bottom:2px solid rgba(201,162,39,.55);border-left:2px solid rgba(201,162,39,.55)"></div>'
        f'<div style="position:absolute;bottom:36px;right:16px;width:16px;height:16px;'
        f'border-bottom:2px solid rgba(201,162,39,.55);border-right:2px solid rgba(201,162,39,.55)"></div>'

        f'<div style="position:relative;display:grid;grid-template-columns:40% 60%;min-height:260px">'

        f'<div style="padding:2.25rem 1.5rem 1.75rem 2rem;display:flex;flex-direction:column;'
        f'justify-content:flex-end;border-right:1px solid rgba(255,255,255,.04);'
        f'background:linear-gradient(135deg,{wash_hi} 0%,{wash_lo} 55%,transparent 100%)">'
        f'<div style="font-size:.55rem;font-weight:800;letter-spacing:.22em;'
        f'text-transform:uppercase;color:rgba(201,162,39,.5);margin-bottom:1.4rem">'
        f'Maior favorita &nbsp;&middot;&nbsp; Copa do Mundo 2026</div>'
        f'{flag_el}'
        f'<div style="font-size:2.4rem;font-weight:900;letter-spacing:-.04em;'
        f'color:{T1};line-height:1;text-transform:uppercase">{team}</div>'
        f'</div>'

        f'<div style="padding:2.25rem 2rem 1.75rem 2.25rem;display:flex;'
        f'flex-direction:column;justify-content:center">'
        f'<div style="font-size:.55rem;font-weight:800;letter-spacing:.2em;'
        f'text-transform:uppercase;color:{T3};margin-bottom:.2rem">Probabilidade de t&iacute;tulo</div>'
        f'<div style="line-height:1;margin-bottom:.2rem">{num_span}</div>'
        f'<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:.35rem;margin:.7rem 0 1rem">'
        f'<div style="background:rgba(255,255,255,.05);border:1px solid rgba(123,159,190,.1);'
        f'border-radius:7px;padding:.45rem .35rem;text-align:center">'
        f'<div style="font-size:.9rem;font-weight:900;color:{T1};font-variant-numeric:tabular-nums">{n // 1000}k</div>'
        f'<div style="font-size:.5rem;font-weight:700;letter-spacing:.06em;text-transform:uppercase;'
        f'color:{T3};margin-top:.1rem">simula&ccedil;&otilde;es</div>'
        f'</div>'
        f'<div style="background:rgba(255,255,255,.05);border:1px solid rgba(123,159,190,.1);'
        f'border-radius:7px;padding:.45rem .35rem;text-align:center">'
        f'<div style="font-size:.9rem;font-weight:900;color:{T1};font-variant-numeric:tabular-nums">{n_historico:,}</div>'
        f'<div style="font-size:.5rem;font-weight:700;letter-spacing:.06em;text-transform:uppercase;'
        f'color:{T3};margin-top:.1rem">jogos hist&oacute;ricos</div>'
        f'</div>'
        f'<div style="background:rgba(255,255,255,.05);border:1px solid rgba(123,159,190,.1);'
        f'border-radius:7px;padding:.45rem .35rem;text-align:center">'
        f'<div style="font-size:.72rem;font-weight:900;color:{T1};line-height:1.2">ELO + XGBoost</div>'
        f'<div style="font-size:.5rem;font-weight:700;letter-spacing:.06em;text-transform:uppercase;'
        f'color:{T3};margin-top:.15rem">desde 1930</div>'
        f'</div>'
        f'</div>'
        f'<div style="display:flex;flex-wrap:wrap;gap:.4rem">{runner_pills}</div>'
        f'</div>'

        f'</div>'

        f'<div style="position:relative;padding:.7rem 1.75rem;'
        f'background:rgba(0,0,0,.28);border-top:1px solid rgba(255,255,255,.04);'
        f'display:flex;align-items:center;gap:.5rem">'
        f'<span style="width:6px;height:6px;border-radius:50%;background:{GREEN};'
        f'display:inline-block;flex-shrink:0"></span>'
        f'<span style="font-size:.63rem;color:rgba(237,242,255,.58);letter-spacing:.04em">'
        f'{n_alive} sele&ccedil;&otilde;es vivas &nbsp;&middot;&nbsp; {phase_name} &nbsp;&middot;&nbsp; {data_max}'
        f'</span></div>'

        f'</div>'
    )


# ── Matchup cards ─────────────────────────────────────────────────────────────

_STAGE_LABELS = {
    "quarter-final":    "Quartas de Final",
    "semi-final":       "Semifinal",
    "third-place match":"Terceiro Lugar",
    "final":            "Final",
}


def _matchup_cards_html(matchups: list) -> str:
    if not matchups:
        return ""

    # Group matchups by stage, preserving chronological order
    seen_stages: list = []
    by_stage: dict = {}
    for m in matchups:
        s = m["stage"]
        if s not in by_stage:
            by_stage[s] = []
            seen_stages.append(s)
        by_stage[s].append(m)

    sections = ""
    for idx, stage_raw in enumerate(seen_stages):
        stage_label = _STAGE_LABELS.get(stage_raw, stage_raw.title()).upper()
        mt          = "margin-top:.9rem;" if idx > 0 else ""
        cards       = ""

        for m in by_stage[stage_raw]:
            h      = m["home_team"]
            a      = m["away_team"]
            nc_h   = get_nation_color(h)
            nc_a   = get_nation_color(a)
            code_h = get_team_code(h)
            code_a = get_team_code(a)
            ph     = m["prob_home"] * 100
            pd_    = m["prob_draw"] * 100
            pa     = m["prob_away"] * 100
            date_l = m["date_label"]
            elo_h  = m["elo_home"]
            elo_a  = m["elo_away"]

            url_h = get_flag_url(h)
            url_a = get_flag_url(a)

            img_h = (
                f'<img src="{url_h}" alt="{h}" style="width:48px;height:auto;border-radius:4px;'
                f'display:block;margin:0 auto;box-shadow:0 3px 10px rgba(0,0,0,.45);'
                f'border:1px solid rgba(255,255,255,.08)">'
                if url_h else
                f'<div style="font-size:2.2rem;line-height:1;text-align:center">{get_flag(h)}</div>'
            )
            img_a = (
                f'<img src="{url_a}" alt="{a}" style="width:48px;height:auto;border-radius:4px;'
                f'display:block;margin:0 auto;box-shadow:0 3px 10px rgba(0,0,0,.45);'
                f'border:1px solid rgba(255,255,255,.08)">'
                if url_a else
                f'<div style="font-size:2.2rem;line-height:1;text-align:center">{get_flag(a)}</div>'
            )

            prob_bar = (
                f'<div style="height:4px;background:{BG3};border-radius:999px;'
                f'overflow:hidden;display:flex;margin-top:.5rem">'
                f'<div style="width:{ph:.1f}%;background:{nc_h};height:100%"></div>'
                f'<div style="width:{pd_:.1f}%;background:rgba(123,159,190,.18);height:100%"></div>'
                f'<div style="width:{pa:.1f}%;background:{nc_a};height:100%"></div>'
                f'</div>'
            )

            diff = abs(ph - pa)
            if diff < 10:
                badge_text  = "Equil&iacute;brio total"
                badge_color = T3
                badge_bg    = "rgba(61,90,118,.18)"
            elif diff < 25:
                badge_text  = "Levemente favorito"
                badge_color = T2
                badge_bg    = "rgba(123,159,190,.1)"
            else:
                badge_text  = "Favorito claro"
                badge_color = GOLD
                badge_bg    = "rgba(201,162,39,.1)"

            badge_html = (
                f'<div style="text-align:center;margin-top:.45rem">'
                f'<span style="font-size:.48rem;font-weight:800;letter-spacing:.1em;'
                f'text-transform:uppercase;color:{badge_color};background:{badge_bg};'
                f'border-radius:999px;padding:.15rem .5rem">'
                f'{badge_text}'
                f'</span>'
                f'</div>'
            )

            cards += (
                f'<div style="background:{BG1};border:1px solid {BORDER};'
                f'border-radius:12px;overflow:hidden">'
                f'<div style="height:3px;background:linear-gradient(90deg,{nc_h} 50%,{nc_a} 50%)"></div>'
                f'<div style="padding:.85rem .7rem .8rem">'
                f'<div style="font-size:.52rem;font-weight:700;letter-spacing:.1em;'
                f'text-transform:uppercase;color:{T3};text-align:center;margin-bottom:.7rem">{date_l}</div>'
                f'<div style="display:grid;grid-template-columns:1fr auto 1fr;align-items:center;gap:.25rem">'
                f'<div style="text-align:center">'
                f'{img_h}'
                f'<div style="font-size:.72rem;font-weight:900;letter-spacing:.04em;'
                f'color:{T1};margin-top:.3rem">{code_h}</div>'
                f'<div style="font-size:.55rem;color:{T3};font-variant-numeric:tabular-nums">ELO {elo_h}</div>'
                f'</div>'
                f'<div style="font-size:.5rem;font-weight:800;letter-spacing:.12em;color:{T2};'
                f'text-transform:uppercase;background:{BG3};border-radius:4px;padding:.18rem .28rem">VS</div>'
                f'<div style="text-align:center">'
                f'{img_a}'
                f'<div style="font-size:.72rem;font-weight:900;letter-spacing:.04em;'
                f'color:{T1};margin-top:.3rem">{code_a}</div>'
                f'<div style="font-size:.55rem;color:{T3};font-variant-numeric:tabular-nums">ELO {elo_a}</div>'
                f'</div>'
                f'</div>'
                f'<div style="display:flex;justify-content:space-between;margin-top:.6rem">'
                f'<span style="font-size:.68rem;font-weight:800;color:{T1};'
                f'font-variant-numeric:tabular-nums">{ph:.0f}%</span>'
                f'<span style="font-size:.6rem;color:{T3}">Emp {pd_:.0f}%</span>'
                f'<span style="font-size:.68rem;font-weight:800;color:{T1};'
                f'font-variant-numeric:tabular-nums">{pa:.0f}%</span>'
                f'</div>'
                + prob_bar
                + badge_html
                + f'</div>'
                f'</div>'
            )

        sections += (
            f'<div style="{mt}display:flex;align-items:center;gap:.75rem;margin-bottom:.7rem">'
            f'<span style="font-size:.6rem;font-weight:800;letter-spacing:.18em;'
            f'text-transform:uppercase;color:{T3}">{stage_label}</span>'
            f'<div style="flex:1;height:1px;background:{BORDER}"></div>'
            f'</div>'
            f'<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:.55rem">'
            + cards +
            f'</div>'
        )

    return f'<div style="margin-bottom:1.5rem">{sections}</div>'


# ── Ranking com tiers visuais ─────────────────────────────────────────────────

_ELIM_RED = "#EF4444"


def _ranking_html(prob_campea: pd.Series, eliminated: list | None = None) -> str:
    max_p = prob_campea.iloc[0] if len(prob_campea) > 0 else 1
    rows  = ""

    for i, (team, p) in enumerate(prob_campea.items(), 1):
        flag_url   = get_flag_url(team)
        flag_emoji = get_flag(team)
        pct        = p * 100
        bar_pct    = (p / max_p * 100) if max_p > 0 else 0

        if flag_url:
            flag_el = (
                f'<img src="{flag_url}" alt="{team}" '
                f'style="width:24px;height:15px;object-fit:cover;border-radius:2px;'
                f'vertical-align:middle;flex-shrink:0">'
            )
        else:
            flag_el = f'<span style="font-size:.9rem;line-height:1">{flag_emoji}</span>'

        if i == 1:
            rank_color  = GOLD
            rank_size   = ".88rem"
            name_color  = T1
            name_weight = "800"
            name_size   = ".95rem"
            pct_color   = GOLD
            bar_bg      = f"linear-gradient(90deg,{GOLD},#FFE580)"
            row_extra   = (
                f"background:rgba(201,162,39,.05);"
                f"border:1px solid rgba(201,162,39,.12);"
                f"box-shadow:0 0 0 1px rgba(201,162,39,.06);"
            )
        elif i <= 3:
            rank_color  = T2
            rank_size   = ".8rem"
            name_color  = T1
            name_weight = "700"
            name_size   = ".92rem"
            pct_color   = T1
            bar_bg      = f"linear-gradient(90deg,{BLUE},rgba(59,130,246,.55))"
            row_extra   = ""
        else:
            rank_color  = T3
            rank_size   = ".78rem"
            name_color  = T2
            name_weight = "600"
            name_size   = ".9rem"
            pct_color   = T2
            bar_bg      = BLUE
            row_extra   = ""

        rows += (
            f'<div class="copa-row" style="display:grid;'
            f'grid-template-columns:2.5rem 1.75rem 1fr 5rem 7rem;'
            f'gap:.6rem;padding:.65rem 1rem;align-items:center;'
            f'border-radius:8px;{row_extra}">'
            f'<div style="font-size:{rank_size};font-weight:800;'
            f'color:{rank_color};text-align:center;'
            f'font-variant-numeric:tabular-nums">{i}</div>'
            f'<div style="display:flex;align-items:center">{flag_el}</div>'
            f'<div style="font-size:{name_size};font-weight:{name_weight};'
            f'color:{name_color};white-space:nowrap;overflow:hidden;'
            f'text-overflow:ellipsis">{team}</div>'
            f'<div style="font-size:.92rem;font-weight:800;color:{pct_color};'
            f'text-align:right;font-variant-numeric:tabular-nums">{pct:.1f}%</div>'
            f'<div style="height:4px;background:{BG3};border-radius:999px;overflow:hidden">'
            f'<div style="width:{bar_pct:.1f}%;height:100%;border-radius:999px;'
            f'background:{bar_bg}"></div>'
            f'</div>'
            f'</div>'
        )

    if eliminated:
        rows += (
            f'<div style="height:1px;background:{BORDER};'
            f'margin:.5rem 1rem;opacity:.35"></div>'
        )
        for team in eliminated:
            flag_url   = get_flag_url(team)
            flag_emoji = get_flag(team)
            if flag_url:
                flag_el = (
                    f'<img src="{flag_url}" alt="{team}" '
                    f'style="width:24px;height:15px;object-fit:cover;border-radius:2px;'
                    f'vertical-align:middle;flex-shrink:0;filter:grayscale(60%)">'
                )
            else:
                flag_el = f'<span style="font-size:.9rem;line-height:1;opacity:.5">{flag_emoji}</span>'

            rows += (
                f'<div class="copa-row" style="display:grid;'
                f'grid-template-columns:2.5rem 1.75rem 1fr 5rem 7rem;'
                f'gap:.6rem;padding:.6rem 1rem;align-items:center;'
                f'border-radius:8px;opacity:.55">'
                f'<div style="font-size:.82rem;font-weight:900;'
                f'color:{_ELIM_RED};text-align:center">✕</div>'
                f'<div style="display:flex;align-items:center">{flag_el}</div>'
                f'<div style="display:flex;align-items:center;gap:.45rem;overflow:hidden">'
                f'<span style="font-size:.9rem;font-weight:600;color:{T3};'
                f'white-space:nowrap;overflow:hidden;text-overflow:ellipsis">{team}</span>'
                f'<span style="font-size:.42rem;font-weight:800;letter-spacing:.08em;'
                f'text-transform:uppercase;color:{_ELIM_RED};'
                f'background:rgba(239,68,68,.12);border-radius:999px;'
                f'padding:.1rem .4rem;flex-shrink:0">Eliminada</span>'
                f'</div>'
                f'<div style="font-size:.88rem;font-weight:700;color:{T3};'
                f'text-align:right">–</div>'
                f'<div style="height:4px;background:{BG3};border-radius:999px"></div>'
                f'</div>'
            )

    return f"<style>.copa-row:hover{{background:{BG2}!important}}</style>{rows}"


# ── render ────────────────────────────────────────────────────────────────────

def render(prob_campea: pd.Series, phase_probs: pd.DataFrame,
           n_simulacoes: int, n_alive: int, phase_name: str, data_max: str,
           matchups=None, n_historico: int = 0, eliminated_qf: list | None = None):

    top1_team = prob_campea.index[0]
    top1_prob = prob_campea.iloc[0] * 100
    runners   = [(t, p * 100) for t, p in prob_campea.iloc[1:4].items()]

    # 1. Onde estamos no torneio
    st.markdown(_progress_strip_html(phase_name), unsafe_allow_html=True)

    # 2. Snapshot editorial
    st.markdown(_snapshot_html(n_alive, top1_team, top1_prob), unsafe_allow_html=True)

    # 3. Confrontos da fase atual (main event)
    if matchups:
        st.markdown(_matchup_cards_html(matchups), unsafe_allow_html=True)

    # 4. Hero — quem é o favorito
    st.markdown(
        _hero_html(top1_team, top1_prob, n_simulacoes, n_alive, phase_name, data_max,
                   runners, n_historico=n_historico),
        unsafe_allow_html=True,
    )

    # 5. Ranking
    st.markdown(
        f"<p style='font-size:.72rem;color:{T3};text-transform:uppercase;"
        f"letter-spacing:.12em;font-weight:700;margin-bottom:.25rem'>Ranking &middot; Top 8</p>",
        unsafe_allow_html=True,
    )
    st.markdown(_ranking_html(prob_campea, eliminated=eliminated_qf), unsafe_allow_html=True)

    with st.expander("Ver todas as seleções"):
        full = prob_campea.reset_index()
        full.columns = ["Seleção", "Probabilidade"]
        full.insert(0, "Pos.", range(1, len(full) + 1))
        full["Bandeira"]      = full["Seleção"].apply(get_flag)
        full["Probabilidade"] = (full["Probabilidade"] * 100).round(1).astype(str) + "%"
        st.dataframe(
            full[["Pos.", "Bandeira", "Seleção", "Probabilidade"]],
            hide_index=True,
            width="stretch",
        )

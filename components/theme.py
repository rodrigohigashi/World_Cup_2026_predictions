from components.flags import EMOJI_FONT

# Background layers
BG0    = "#06101D"
BG1    = "#0C1A2E"
BG2    = "#132338"
BG3    = "#1C3050"

# Accent
GOLD   = "#C9A227"
GREEN  = "#22C55E"
RED    = "#EF4444"
BLUE   = "#3B82F6"

# Text
T1     = "#EDF2FF"
T2     = "#7B9FBE"
T3     = "#6B90AD"
BORDER = "rgba(123,159,190,0.11)"

_AXIS = dict(
    gridcolor="rgba(123,159,190,0.08)",
    zerolinecolor="rgba(123,159,190,0.12)",
    tickfont=dict(color=T2),
    title_font=dict(color=T3),
)

def apply_theme(fig):
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=T2, family=EMOJI_FONT),
    )
    fig.update_xaxes(**_AXIS)
    fig.update_yaxes(**_AXIS)
    return fig

def section_header_html(title: str, subtitle: str = "") -> str:
    sub = (
        f'<p style="margin:.45rem 0 0;font-size:.9rem;color:{T2};line-height:1.55">'
        f'{subtitle}</p>'
    ) if subtitle else ""
    return (
        f'<div style="margin:0 0 1.25rem">'
        f'<h2 style="margin:0;font-size:1.4rem;font-weight:900;letter-spacing:-.025em;'
        f'color:{T1};line-height:1.2">{title}</h2>{sub}</div>'
    )

def caption_html(text: str) -> str:
    return (
        f'<p style="margin:.35rem 0 .9rem;font-size:.72rem;'
        f'color:{T3};line-height:1.5">{text}</p>'
    )

def alert_html(body: str) -> str:
    return (
        f'<div style="background:rgba(201,162,39,.07);border-left:3px solid {GOLD};'
        f'border-radius:0 8px 8px 0;padding:.9rem 1.15rem;margin:.75rem 0">'
        f'<p style="margin:0;font-size:.85rem;color:{T2};line-height:1.55">'
        f'⚠&nbsp; {body}</p></div>'
    )

def pill_html(text: str, variant: str = "muted") -> str:
    _map = {
        "gold":  (f"rgba(201,162,39,.15)",  GOLD),
        "green": (f"rgba(34,197,94,.15)",   GREEN),
        "red":   (f"rgba(239,68,68,.15)",   RED),
        "blue":  (f"rgba(59,130,246,.15)",  BLUE),
        "muted": (BG3,                       T3),
    }
    bg, color = _map.get(variant, _map["muted"])
    return (
        f'<span style="display:inline-flex;align-items:center;padding:.15rem .55rem;'
        f'border-radius:999px;font-size:.62rem;font-weight:700;letter-spacing:.06em;'
        f'text-transform:uppercase;background:{bg};color:{color};white-space:nowrap">'
        f'{text}</span>'
    )
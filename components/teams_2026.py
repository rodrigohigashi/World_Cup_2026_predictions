"""
Seleções classificadas para a Copa do Mundo FIFA 2026.
Lista oficial com 48 times, usando os nomes do banco Fjelstul (1930-2022)
para compatibilidade com os ratings ELO históricos.

Times sem histórico em Copa (Curaçao, Cabo Verde, Congo DR, Uzbekistão, Jordânia)
recebem ELO padrão 1500 na simulação.

Quais times ainda estão vivos é derivado automaticamente em data_loader._alive_teams()
a partir dos resultados registrados em wc2026_matches.csv — sem lista manual.
"""

TEAMS_2026 = [
    # ── CONCACAF (6 vagas) ────────────────────────────────────────────────────
    "United States",          # sede
    "Mexico",                 # sede
    "Canada",                 # sede
    "Panama",
    "Haiti",
    "Curaçao",                # estreante — sem ELO histórico

    # ── AFC / Ásia (9 vagas) ─────────────────────────────────────────────────
    "Japan",
    "South Korea",
    "Iran",
    "Saudi Arabia",
    "Australia",
    "Uzbekistan",             # estreante — sem ELO histórico
    "Jordan",                 # estreante — sem ELO histórico
    "Iraq",
    "Qatar",

    # ── CAF / África (10 vagas) ──────────────────────────────────────────────
    "Morocco",
    "Senegal",
    "Egypt",
    "South Africa",
    "Algeria",
    "Tunisia",
    "Ghana",
    "Ivory Coast",            # nome no banco Fjelstul (= Côte d'Ivoire)
    "Cabo Verde",             # estreante — sem ELO histórico
    "Congo DR",               # estreante no nome atual — sem ELO histórico

    # ── CONMEBOL / América do Sul (6 vagas) ──────────────────────────────────
    "Argentina",
    "Brazil",
    "Colombia",
    "Ecuador",
    "Paraguay",
    "Uruguay",

    # ── OFC / Oceania (1 vaga — playoff intercontinental) ────────────────────
    "New Zealand",

    # ── UEFA / Europa (16 vagas) ─────────────────────────────────────────────
    "France",
    "England",
    "Germany",
    "Spain",
    "Portugal",
    "Netherlands",
    "Turkey",
    "Croatia",
    "Switzerland",
    "Austria",
    "Scotland",
    "Belgium",
    "Norway",
    "Sweden",
    "Bosnia and Herzegovina",
    "Czech Republic",         # nome no banco Fjelstul (= Czechia)
]


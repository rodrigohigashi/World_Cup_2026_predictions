"""
Carrega dados, computa ELO, treina modelo e roda simulação.
Tudo cacheado — executa apenas uma vez por sessão do Streamlit.
"""

import numpy as np
import pandas as pd
import streamlit as st
from collections import Counter
from itertools import combinations
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, log_loss
from sklearn.linear_model import LogisticRegression
import xgboost as xgb
import warnings

warnings.filterwarnings("ignore")

DATA_DIR = Path(__file__).parent.parent / "data" / "fjelstul"
N_SIMULACOES = 10_000
FEATURES = ["elo_home", "elo_away", "elo_diff"]
_BYE = "__BYE__"


# ── 1. Dados brutos ──────────────────────────────────────────────────────────

WC2026_PATH = DATA_DIR.parent / "wc2026_matches.csv"

COLS = [
    "match_id", "match_date", "tournament_name", "stage_name",
    "group_stage", "knockout_stage",
    "home_team_name", "away_team_name",
    "home_team_score", "away_team_score",
    "home_team_win", "away_team_win", "draw", "result",
]

@st.cache_data
def load_matches() -> pd.DataFrame:
    # Fjelstul: Copas Masculinas 1930–2022
    hist = pd.read_csv(DATA_DIR / "matches.csv", low_memory=False)
    hist["match_date"] = pd.to_datetime(hist["match_date"])
    # Filtra apenas Copa do Mundo Masculina — o banco Fjelstul contém
    # também a Copa Feminina (1991-2019), que inflacionaria o ELO de
    # seleções com times femininos fortes (EUA, Japão, Noruega, Suécia).
    hist = hist[hist["tournament_name"].str.contains("Men's", na=False)][COLS]

    # Dados reais da Copa 2026 (fase de grupos completa + R32 completo + R16 parcial)
    frames = [hist]
    if WC2026_PATH.exists():
        wc26 = pd.read_csv(WC2026_PATH)
        wc26["match_date"] = pd.to_datetime(wc26["match_date"])
        frames.append(wc26[COLS])

    return pd.concat(frames, ignore_index=True).sort_values("match_date").reset_index(drop=True)


# ── 2. ELO ───────────────────────────────────────────────────────────────────

def _expected(elo_a, elo_b):
    return 1 / (1 + 10 ** ((elo_b - elo_a) / 400))

def _update(elo_a, elo_b, score_a, k=30):
    return elo_a + k * (score_a - _expected(elo_a, elo_b))

@st.cache_data
def compute_elo(matches: pd.DataFrame):
    ratings = {}
    elo_home, elo_away = [], []

    for _, row in matches.iterrows():
        h, a = row["home_team_name"], row["away_team_name"]
        eh = ratings.get(h, 1500)
        ea = ratings.get(a, 1500)
        elo_home.append(eh)
        elo_away.append(ea)

        if row["result"] == "scheduled":
            continue  # skip unplayed fixtures — don't corrupt ELO

        score = 1.0 if row["home_team_win"] else (0.5 if row["draw"] else 0.0)
        ratings[h] = _update(eh, ea, score)
        ratings[a] = _update(ea, eh, 1 - score)

    matches = matches.copy()
    matches["elo_home"] = elo_home
    matches["elo_away"] = elo_away
    matches["elo_diff"] = matches["elo_home"] - matches["elo_away"]

    result_map = {"home team win": 0, "draw": 1, "away team win": 2}
    matches["result_label"] = matches["result"].map(result_map)

    ranking = pd.Series(ratings).sort_values(ascending=False)
    return matches, ratings, ranking


# ── 3. Modelos ───────────────────────────────────────────────────────────────

@st.cache_resource
def train_models(matches: pd.DataFrame):
    df = matches.dropna(subset=FEATURES + ["result_label"]).copy()
    X = df[FEATURES]
    y = df["result_label"].astype(int)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    # XGBoost
    xgb_model = xgb.XGBClassifier(
        n_estimators=300, max_depth=3, learning_rate=0.05,
        objective="multi:softprob", num_class=3,
        eval_metric="mlogloss", random_state=42,
        early_stopping_rounds=20,
    )
    xgb_model.fit(X_train, y_train, eval_set=[(X_test, y_test)], verbose=False)

    # Regressão Logística (baseline)
    lr_model = LogisticRegression(max_iter=500, random_state=42)
    lr_model.fit(X_train, y_train)

    # Métricas comparativas
    metrics = {
        "XGBoost": {
            "accuracy": accuracy_score(y_test, xgb_model.predict(X_test)),
            "log_loss": log_loss(y_test, xgb_model.predict_proba(X_test)),
        },
        "Regressão Logística": {
            "accuracy": accuracy_score(y_test, lr_model.predict(X_test)),
            "log_loss": log_loss(y_test, lr_model.predict_proba(X_test)),
        },
    }

    return xgb_model, lr_model, metrics, X_test, y_test


# ── 4. Detecção de out-of-distribution (OOD) ────────────────────────────────

@st.cache_data
def build_ood_detector(_booster, matches: pd.DataFrame, percentile: int = 5):
    """
    Constrói um detector OOD baseado em Mean Leaf Sample Count (MLSC).

    Para cada previsão, conta quantas amostras de treino caem na mesma folha
    que o ponto de teste em cada uma das 300 árvores, e calcula a média.
    Um MLSC baixo indica região de baixa cobertura nos dados de treino
    (extrapolação), onde o XGBoost é menos confiável.

    Retorna:
      leaf_counters : list[Counter] — contagem por (árvore, folha)
      threshold     : float         — p{percentile} do MLSC no treino
    """
    df = matches.dropna(subset=FEATURES + ["result_label"]).copy()
    X_all = df[FEATURES]
    y_all = df["result_label"].astype(int)
    X_train, _, y_train, _ = train_test_split(
        X_all, y_all, test_size=0.2, random_state=42, stratify=y_all
    )

    X_train_arr = X_train.values.astype(np.float32)
    dm_train = xgb.DMatrix(X_train_arr, feature_names=FEATURES)
    train_leaves = _booster.predict(dm_train, pred_leaf=True)   # (n_train, n_trees)
    n_trees = train_leaves.shape[1]

    leaf_counters = [Counter(train_leaves[:, t].tolist()) for t in range(n_trees)]

    n_train = len(X_train)
    mlsc_train = np.array([
        np.mean([leaf_counters[t][int(train_leaves[i, t])] for t in range(n_trees)])
        for i in range(n_train)
    ])
    threshold = float(np.percentile(mlsc_train, percentile))
    return leaf_counters, threshold


def _mlsc(leaf_counters: list, booster, row_arr: list) -> float:
    """Mean Leaf Sample Count para um ponto de teste (1 amostra)."""
    dm = xgb.DMatrix(np.array([row_arr], dtype=np.float32), feature_names=FEATURES)
    leaves = booster.predict(dm, pred_leaf=True)[0]
    return float(np.mean([leaf_counters[t][int(leaves[t])] for t in range(len(leaf_counters))]))


def _prever_neutro_hibrido(xgb_model, lr_model, leaf_counters, threshold, e1, e2):
    """
    Previsão neutra híbrida: avalia cada direção independentemente e usa LR
    quando o MLSC cai abaixo do limiar de cobertura do treino.

    Preserva a simetria de campo neutro — a média das duas direções garante
    P(A vence | A-manda) + P(A vence | B-manda) / 2 = P(A vence, campo neutro).
    """
    booster = xgb_model.get_booster()
    row_A = [e1, e2, e1 - e2]
    row_B = [e2, e1, e2 - e1]
    m_A = lr_model if _mlsc(leaf_counters, booster, row_A) < threshold else xgb_model
    m_B = lr_model if _mlsc(leaf_counters, booster, row_B) < threshold else xgb_model
    ph_A, pd_A, pa_A = _prever(m_A, e1, e2)
    ph_B, pd_B, pa_B = _prever(m_B, e2, e1)
    return (ph_A + pa_B) / 2, (pd_A + pd_B) / 2, (pa_A + ph_B) / 2


# ── 5. Simulação Monte Carlo ─────────────────────────────────────────────────

def _prever(model, e1, e2):
    X = np.array([[e1, e2, e1 - e2]])
    p = model.predict_proba(X)[0]
    return p[0], p[1], p[2]  # home_win, draw, away_win

def _prever_neutral(model, e1, e2):
    """Previsão para campo neutro: média das duas direções cancela o home bias."""
    ph, pd, pa = _prever(model, e1, e2)
    qh, qd, qa = _prever(model, e2, e1)
    return (ph + qa) / 2, (pd + qd) / 2, (pa + qh) / 2

def _simular_jogo(ph, pd_, pa):
    r = np.random.random()
    if r < ph:
        return "home"
    elif r < ph + pd_:
        return "home" if np.random.random() < 0.5 else "away"
    return "away"

def _alive_teams(matches: pd.DataFrame) -> set:
    """
    Deriva automaticamente quais seleções ainda estão na Copa 2026.

    Regras (aplicadas apenas a jogos de 2026):
      1. Perdeu jogo de mata-mata → eliminada.
      2. Nunca apareceu em nenhum jogo de 2026 → excluída (ex: Turkey, Scotland).
      3. Aparece em exatamente 3 jogos de fase de grupos (grupo completo no CSV)
         mas nunca apareceu em jogo de mata-mata → eliminada na fase de grupos.
         Regra 3 só vale quando já existem jogos de mata-mata (fase encerrada).
      4. Todos os demais → vivas.

    Grupos com dados incompletos (<3 jogos por time no CSV) ficam com status
    incerto e são mantidos no pool — filtrados pelo ELO se necessário.
    """
    from collections import Counter

    m26 = matches[matches["match_date"] >= "2026-01-01"]
    appeared = set(m26["home_team_name"]) | set(m26["away_team_name"])

    ko = m26[m26["knockout_stage"] == 1]

    # Regra 1: perdedores de mata-mata
    eliminated = set()
    eliminated.update(ko[ko["result"] == "away team win"]["home_team_name"])
    eliminated.update(ko[ko["result"] == "home team win"]["away_team_name"])

    # Regra 3: grupos completos — times sem nenhuma aparição no mata-mata
    # Em grupos round-robin de 4 times, cada seleção joga exatamente 3 partidas.
    # Se count == 3 e a fase knockout já começou, temos dados completos do grupo
    # e o time não avançou (caso contrário apareceria no knockout).
    if len(ko) > 0:
        gs = m26[m26["group_stage"] == 1]
        gs_counts = Counter(list(gs["home_team_name"]) + list(gs["away_team_name"]))
        in_ko = set(ko["home_team_name"]) | set(ko["away_team_name"])
        for team, count in gs_counts.items():
            if count == 3 and team not in in_ko:
                eliminated.add(team)

    return appeared - eliminated


def _make_bracket(teams: list, n_byes: int, bracket_size: int) -> list:
    """
    Embaralha times reais e distribui BYEs em pares distintos.
    Garante por construção que nunca há um par BYE×BYE.
    """
    shuffled = list(teams)
    np.random.shuffle(shuffled)
    if n_byes == 0:
        return shuffled
    bye_pairs = np.random.choice(bracket_size // 2, n_byes, replace=False)
    bracket = [None] * bracket_size
    for bp in bye_pairs:
        bracket[2 * bp + 1] = _BYE
    ri = 0
    for i in range(bracket_size):
        if bracket[i] is None:
            bracket[i] = shuffled[ri]
            ri += 1
    return bracket


def get_current_stage_matches(
    matches: pd.DataFrame,
    elo_ratings: dict,
    model,
    lr_model=None,
    ood_params=None,
) -> list:
    """
    Returns upcoming fixtures for the current stage.

    Reads rows where result='scheduled' from the 2026 portion of the dataset.
    Automatically advances to the next stage as the user adds results and new
    fixture rows to wc2026_matches.csv — no code changes required.

    When lr_model and ood_params=(leaf_counters, threshold) are provided,
    uses the hybrid OOD-aware predictor for each matchup.

    Returns a list of dicts:
      home_team, away_team, date, date_label, stage,
      elo_home, elo_away, prob_home, prob_draw, prob_away
    """
    _DIAS_PT = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]

    m26      = matches[matches["match_date"] >= "2026-01-01"]
    upcoming = m26[m26["result"] == "scheduled"].sort_values("match_date")

    if upcoming.empty:
        return []

    use_hybrid = lr_model is not None and ood_params is not None

    out = []
    for _, row in upcoming.iterrows():
        h   = row["home_team_name"]
        a   = row["away_team_name"]
        eh  = elo_ratings.get(h, 1500)
        ea  = elo_ratings.get(a, 1500)
        if use_hybrid:
            leaf_counters, threshold = ood_params
            pw, pd_, pa = _prever_neutro_hibrido(model, lr_model, leaf_counters, threshold, eh, ea)
        else:
            pw, pd_, pa = _prever_neutral(model, eh, ea)
        dt  = row["match_date"]
        out.append({
            "home_team":  h,
            "away_team":  a,
            "date":       dt,
            "date_label": f"{_DIAS_PT[dt.dayofweek]} · {dt.strftime('%d/%m')}",
            "stage":      row["stage_name"],
            "elo_home":   round(eh),
            "elo_away":   round(ea),
            "prob_home":  pw,
            "prob_draw":  pd_,
            "prob_away":  pa,
        })
    return out


@st.cache_data
def run_simulation(
    _model,
    _elo_ratings,
    _ranking,
    _matches,
    n=N_SIMULACOES,
    seed=42,
    _lr_model=None,
    _ood_params=None,
):
    """
    Roda n simulações do torneio e retorna:
    - prob_campea:  Series  [team → P(campeã)]
    - phase_probs:  DataFrame [team × fase → probabilidade]

    Quando _lr_model e _ood_params=(leaf_counters, threshold) são fornecidos,
    usa o preditor híbrido OOD-aware: XGBoost para pares dentro da distribuição
    de treino, Regressão Logística quando o MLSC cai abaixo do limiar.
    """
    from components.teams_2026 import TEAMS_2026

    use_hybrid = _lr_model is not None and _ood_params is not None

    # Seleções ainda vivas: derivadas automaticamente dos resultados no CSV.
    # Não depende de lista manual — basta adicionar jogos ao wc2026_matches.csv.
    alive = _alive_teams(_matches)

    elo_2026 = {
        t: _elo_ratings.get(t, 1500)
        for t in TEAMS_2026
        if t in alive
    }

    # Bracket na menor potência de 2 >= número de times vivos.
    # Quando n_alive não é potência de 2 (ex: 7 após um QF decidido),
    # slots vagos recebem um BYE que sempre perde — sem cortar times reais.
    n_alive = len(elo_2026)
    bracket_size = 1 << (max(n_alive, 1) - 1).bit_length()
    teams = list(pd.Series(elo_2026).sort_values(ascending=False).index)

    # Pré-computa probabilidades para cada par de times reais
    prob_cache = {}
    for t1, t2 in combinations(teams, 2):
        e1 = elo_2026.get(t1, 1500)
        e2 = elo_2026.get(t2, 1500)
        if use_hybrid:
            leaf_counters, threshold = _ood_params
            ph, pd_, pa = _prever_neutro_hibrido(_model, _lr_model, leaf_counters, threshold, e1, e2)
        else:
            ph, pd_, pa = _prever_neutral(_model, e1, e2)
        prob_cache[(t1, t2)] = (ph, pd_, pa)
        prob_cache[(t2, t1)] = (pa, pd_, ph)  # simétrico por construção

    # BYE: slot fictício que sempre perde — necessário quando n_alive não é potência de 2
    for real_team in teams:
        prob_cache[(_BYE, real_team)] = (0.0, 0.0, 1.0)
        prob_cache[(real_team, _BYE)] = (1.0, 0.0, 0.0)
    n_byes = bracket_size - n_alive

    np.random.seed(seed)

    # Rastreia quantas vezes cada time alcançou cada fase
    phases = ["quartas", "semi", "final", "campeao"]
    counts = {t: {p: 0 for p in phases} for t in teams}

    for _ in range(n):
        bracket = _make_bracket(teams, n_byes, bracket_size)
        # Alinha ao estágio atual: bracket_size=16→0, 8→1, 4→2.
        # phase_idx=0 só é correto quando n_alive=16 (simulação começa na R16).
        # Para bracket menor, as primeiras fases já foram disputadas e o
        # contador deve começar na fase correspondente ao próximo milestone.
        phase_idx = max(0, 5 - bracket_size.bit_length())

        while len(bracket) > 1:
            proxima = []
            for i in range(0, len(bracket), 2):
                h, a = bracket[i], bracket[i + 1]
                ph, pd_, pa = prob_cache[(h, a)]
                venc = h if _simular_jogo(ph, pd_, pa) == "home" else a
                proxima.append(venc)

            if len(proxima) == 1:
                if proxima[0] != _BYE:
                    counts[proxima[0]]["campeao"] += 1
            elif phase_idx < len(phases) - 1:
                for t in proxima:
                    if t != _BYE:
                        counts[t][phases[phase_idx]] += 1

            phase_idx += 1
            bracket = proxima

    phase_probs = pd.DataFrame(counts).T.div(n)
    phase_probs.index.name = "team"
    prob_campea = phase_probs["campeao"].sort_values(ascending=False)

    return prob_campea, phase_probs

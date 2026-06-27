"""
Modelo de previsão de resultado de partida (vitória/empate/derrota)
+ simulador Monte Carlo do torneio completo.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, log_loss
import xgboost as xgb
import pickle

ROOT = Path(__file__).parent.parent
DATA_PROCESSED = ROOT / "data" / "processed"
MODEL_PATH = ROOT / "data" / "processed" / "model.pkl"

FEATURES = [
    "home_win_rate",
    "home_goals_scored_avg",
    "home_goals_conceded_avg",
    "away_win_rate",
    "away_goals_scored_avg",
    "away_goals_conceded_avg",
    "strength_diff",
    "attack_diff",
    "defense_diff",
]


def load_training_data() -> tuple[pd.DataFrame, pd.Series]:
    df = pd.read_parquet(DATA_PROCESSED / "matches_features.parquet")
    df = df.dropna(subset=FEATURES + ["result_label"])
    X = df[FEATURES]
    y = df["result_label"].astype(int)
    return X, y


def train_model():
    X, y = load_training_data()
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    model = xgb.XGBClassifier(
        n_estimators=300,
        max_depth=4,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        objective="multi:softprob",
        num_class=3,
        eval_metric="mlogloss",
        random_state=42,
        early_stopping_rounds=30,
    )

    model.fit(
        X_train, y_train,
        eval_set=[(X_test, y_test)],
        verbose=50,
    )

    preds = model.predict(X_test)
    probs = model.predict_proba(X_test)
    print("\n--- Relatório de Classificação ---")
    print(classification_report(y_test, preds, target_names=["Home Win", "Draw", "Away Win"]))
    print(f"Log-loss: {log_loss(y_test, probs):.4f}")

    with open(MODEL_PATH, "wb") as f:
        pickle.dump(model, f)
    print(f"\nModelo salvo em {MODEL_PATH}")
    return model


def load_model():
    with open(MODEL_PATH, "rb") as f:
        return pickle.load(f)


def predict_match(
    model,
    home_win_rate: float,
    home_goals_scored: float,
    home_goals_conceded: float,
    away_win_rate: float,
    away_goals_scored: float,
    away_goals_conceded: float,
) -> dict:
    """Retorna probabilidades {home_win, draw, away_win} para um jogo."""
    row = pd.DataFrame([{
        "home_win_rate": home_win_rate,
        "home_goals_scored_avg": home_goals_scored,
        "home_goals_conceded_avg": home_goals_conceded,
        "away_win_rate": away_win_rate,
        "away_goals_scored_avg": away_goals_scored,
        "away_goals_conceded_avg": away_goals_conceded,
        "strength_diff": home_win_rate - away_win_rate,
        "attack_diff": home_goals_scored - away_goals_scored,
        "defense_diff": home_goals_conceded - away_goals_conceded,
    }])
    probs = model.predict_proba(row)[0]
    return {"home_win": probs[0], "draw": probs[1], "away_win": probs[2]}


def simulate_match(probs: dict) -> str:
    """Retorna 'home' ou 'away' (sem empate — usado nas fases eliminatórias)."""
    r = np.random.random()
    # Em mata-mata, empate vai a pênaltis (50/50 entre os dois)
    if r < probs["home_win"]:
        return "home"
    elif r < probs["home_win"] + probs["draw"]:
        return "home" if np.random.random() < 0.5 else "away"
    else:
        return "away"


def run_tournament_simulation(
    bracket: list[tuple],  # [(home_team, home_stats, away_team, away_stats), ...]
    model,
    n_simulations: int = 10_000,
) -> pd.Series:
    """
    Simula o torneio completo N vezes.
    bracket: lista de confrontos do chaveamento atual (oitavas, quartas, etc.)
    Retorna contagem de títulos por seleção.
    """
    champion_counts = {}

    for _ in range(n_simulations):
        teams = list(bracket)  # lista de tuplas (home, stats_h, away, stats_a)
        while len(teams) > 1:
            next_round = []
            for i in range(0, len(teams), 2):
                home_name, hs, away_name, as_ = teams[i]
                probs = predict_match(model, *hs, *as_)
                winner = simulate_match(probs)
                if winner == "home":
                    next_round.append((home_name, hs, None, None))
                else:
                    next_round.append((away_name, as_, None, None))
            teams = next_round

        champion = teams[0][0]
        champion_counts[champion] = champion_counts.get(champion, 0) + 1

    return (
        pd.Series(champion_counts)
        .sort_values(ascending=False)
        .div(n_simulations)
        .rename("prob_campeo")
    )


if __name__ == "__main__":
    print("Treinando modelo...")
    model = train_model()

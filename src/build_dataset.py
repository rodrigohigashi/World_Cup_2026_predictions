"""
Constrói dataset unificado de partidas com features para o modelo.
Fonte: Fjelstul (histórico 1930-2022) + Kaggle 2026 (ao vivo, quando disponível).
"""

import pandas as pd
import numpy as np
from pathlib import Path

ROOT = Path(__file__).parent.parent
DATA_FJELSTUL = ROOT / "data" / "fjelstul"
DATA_KAGGLE = ROOT / "data" / "kaggle_2026"
DATA_PROCESSED = ROOT / "data" / "processed"


def load_fjelstul_matches() -> pd.DataFrame:
    matches = pd.read_csv(DATA_FJELSTUL / "matches.csv", low_memory=False)

    # Resultado numérico: 0=home win, 1=draw, 2=away win
    result_map = {"home team win": 0, "draw": 1, "away team win": 2}
    matches["result_label"] = matches["result"].map(result_map)

    # Manter apenas colunas relevantes
    cols = [
        "tournament_id", "tournament_name", "match_id", "match_date",
        "stage_name", "group_stage", "knockout_stage",
        "home_team_name", "away_team_name",
        "home_team_score", "away_team_score",
        "home_team_win", "away_team_win", "draw",
        "result_label",
    ]
    df = matches[cols].copy()
    df["match_date"] = pd.to_datetime(df["match_date"])
    df = df.sort_values("match_date").reset_index(drop=True)

    print(f"Fjelstul: {len(df)} partidas carregadas (1930–2022)")
    return df


def compute_rolling_stats(matches: pd.DataFrame, window: int = 10) -> pd.DataFrame:
    """
    Cria stats acumuladas por seleção antes de cada jogo:
    win_rate, goals_scored_avg, goals_conceded_avg.
    """
    # Expandir para perspectiva por time (cada jogo gera 2 linhas)
    home_rows = matches[["match_id", "match_date", "home_team_name",
                          "away_team_name", "home_team_score", "away_team_score",
                          "home_team_win"]].copy()
    home_rows.columns = ["match_id", "match_date", "team", "opponent",
                         "goals_for", "goals_against", "win"]

    away_rows = matches[["match_id", "match_date", "away_team_name",
                          "home_team_name", "away_team_score", "home_team_score",
                          "away_team_win"]].copy()
    away_rows.columns = ["match_id", "match_date", "team", "opponent",
                         "goals_for", "goals_against", "win"]

    team_df = pd.concat([home_rows, away_rows], ignore_index=True)
    team_df = team_df.sort_values(["team", "match_date"]).reset_index(drop=True)

    # Rolling com shift(1) para evitar vazamento de dados
    grp = team_df.groupby("team")
    team_df["win_rate"]          = grp["win"].transform(
        lambda x: x.shift(1).rolling(window, min_periods=1).mean())
    team_df["goals_scored_avg"]  = grp["goals_for"].transform(
        lambda x: x.shift(1).rolling(window, min_periods=1).mean())
    team_df["goals_conceded_avg"] = grp["goals_against"].transform(
        lambda x: x.shift(1).rolling(window, min_periods=1).mean())

    return team_df[["match_id", "team", "win_rate", "goals_scored_avg", "goals_conceded_avg"]]


def build_match_features(matches: pd.DataFrame) -> pd.DataFrame:
    stats = compute_rolling_stats(matches)

    # Stats do time da casa
    home_stats = stats.merge(
        matches[["match_id", "home_team_name"]],
        on="match_id"
    ).query("team == home_team_name").rename(columns={
        "win_rate":           "home_win_rate",
        "goals_scored_avg":   "home_goals_scored_avg",
        "goals_conceded_avg": "home_goals_conceded_avg",
    })[["match_id", "home_win_rate", "home_goals_scored_avg", "home_goals_conceded_avg"]]

    # Stats do time visitante
    away_stats = stats.merge(
        matches[["match_id", "away_team_name"]],
        on="match_id"
    ).query("team == away_team_name").rename(columns={
        "win_rate":           "away_win_rate",
        "goals_scored_avg":   "away_goals_scored_avg",
        "goals_conceded_avg": "away_goals_conceded_avg",
    })[["match_id", "away_win_rate", "away_goals_scored_avg", "away_goals_conceded_avg"]]

    df = matches.merge(home_stats, on="match_id", how="left")
    df = df.merge(away_stats, on="match_id", how="left")

    # Features derivadas
    df["strength_diff"] = df["home_win_rate"]          - df["away_win_rate"]
    df["attack_diff"]   = df["home_goals_scored_avg"]  - df["away_goals_scored_avg"]
    df["defense_diff"]  = df["home_goals_conceded_avg"] - df["away_goals_conceded_avg"]

    return df


if __name__ == "__main__":
    DATA_PROCESSED.mkdir(exist_ok=True)

    df = load_fjelstul_matches()
    df = build_match_features(df)

    out = DATA_PROCESSED / "matches_features.parquet"
    df.to_parquet(out, index=False)

    feature_cols = [
        "home_win_rate", "home_goals_scored_avg", "home_goals_conceded_avg",
        "away_win_rate", "away_goals_scored_avg", "away_goals_conceded_avg",
        "strength_diff", "attack_diff", "defense_diff", "result_label",
    ]
    valid = df.dropna(subset=feature_cols)
    print(f"\nDataset salvo em {out}")
    print(f"Shape total: {df.shape} | Com features completas: {len(valid)}")
    print(df[["home_team_name", "away_team_name", "result_label",
              "home_win_rate", "away_win_rate", "strength_diff"]].tail(10).to_string())

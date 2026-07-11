"""
Testes para data_loader.py.

Propriedades verificadas:
1. _make_bracket: nenhum par BYE x BYE (previne KeyError com 6 times).
2. _make_bracket: P(BYE) = n_byes/n_alive para cada time (uniformidade).
3. _prever_neutral: probabilidades invariantes a ordem das equipes (campo neutro).
4. _prever_neutral: probabilidades somam exatamente 1.0.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np
import pytest

from components.data_loader import _BYE, _make_bracket, _prever, _prever_neutral


@pytest.mark.parametrize("n_alive", [4, 5, 6, 7])
def test_no_bye_bye(n_alive: int) -> None:
    """Nenhum par adjacente pode ser BYE x BYE em 5.000 brackets."""
    bracket_size = 1 << (max(n_alive, 1) - 1).bit_length()
    n_byes = bracket_size - n_alive
    teams = [f"T{i}" for i in range(n_alive)]

    np.random.seed(0)
    for iteration in range(5_000):
        bracket = _make_bracket(teams, n_byes, bracket_size)
        for i in range(0, bracket_size, 2):
            if bracket[i] == _BYE and bracket[i + 1] == _BYE:
                pytest.fail(
                    f"BYE x BYE em n_alive={n_alive}, "
                    f"iteracao {iteration}, slots ({i},{i+1}): {bracket}"
                )


@pytest.mark.parametrize("n_alive", [5, 6, 7])
def test_bye_assignment_is_uniform(n_alive: int) -> None:
    """Cada time deve receber BYE com P = n_byes/n_alive (tolerancia 2pp)."""
    bracket_size = 1 << (max(n_alive, 1) - 1).bit_length()
    n_byes = bracket_size - n_alive
    if n_byes == 0:
        return  # sem BYEs, nada a verificar
    teams = [f"T{i}" for i in range(n_alive)]
    expected_p = n_byes / n_alive

    N = 30_000
    bye_counts = {t: 0 for t in teams}
    np.random.seed(0)
    for _ in range(N):
        bracket = _make_bracket(teams, n_byes, bracket_size)
        for i in range(0, bracket_size, 2):
            if bracket[i + 1] == _BYE and bracket[i] != _BYE:
                bye_counts[bracket[i]] += 1

    for team, count in bye_counts.items():
        observed_p = count / N
        assert abs(observed_p - expected_p) < 0.02, (
            f"n_alive={n_alive} | {team}: "
            f"observado {observed_p:.3f}, esperado {expected_p:.3f}"
        )


# ── Testes de _prever_neutral ─────────────────────────────────────────────────

class _MockModel:
    """Modelo mock com home bias forte (70% fixo para home) sem usar ELO."""
    def predict_proba(self, X):
        return np.array([[0.70, 0.15, 0.15]])


def test_prever_neutral_symmetry_unit() -> None:
    """Propriedade matematica: _prever_neutral(e1,e2) e o espelho de _prever_neutral(e2,e1)."""
    model = _MockModel()
    ph, pd, pa = _prever_neutral(model, 1600.0, 1500.0)
    qh, qd, qa = _prever_neutral(model, 1500.0, 1600.0)

    assert abs(ph - qa) < 1e-10, f"P(t1 vence) difere por ordem: {ph:.6f} vs {qa:.6f}"
    assert abs(pd - qd) < 1e-10, f"P(empate) difere por ordem:   {pd:.6f} vs {qd:.6f}"
    assert abs(pa - qh) < 1e-10, f"P(t2 vence) difere por ordem: {pa:.6f} vs {qh:.6f}"


def test_prever_neutral_sums_to_one_unit() -> None:
    """Probabilidades neutras devem somar 1.0."""
    model = _MockModel()
    for e1, e2 in [(1600.0, 1500.0), (1500.0, 1500.0), (1400.0, 1700.0)]:
        ph, pd, pa = _prever_neutral(model, e1, e2)
        assert abs(ph + pd + pa - 1.0) < 1e-10, (
            f"Soma != 1 para ELOs ({e1},{e2}): {ph+pd+pa:.10f}"
        )


def test_prever_neutral_reduces_bias_unit() -> None:
    """O modelo mock tem bias de +55pp. _prever_neutral deve elimina-lo."""
    model = _MockModel()
    ph_raw, _, pa_raw = _prever(model, 1500.0, 1500.0)
    assert abs(ph_raw - pa_raw) > 0.50, "Mock deveria ter bias alto"

    ph_n, _, pa_n = _prever_neutral(model, 1500.0, 1500.0)
    assert abs(ph_n - pa_n) < 1e-10, (
        f"Bias nao eliminado: home={ph_n:.4f} away={pa_n:.4f}"
    )


@pytest.mark.parametrize("t1,t2", [
    ("England",   "Norway"),
    ("Argentina", "Switzerland"),
    ("Spain",     "France"),
])
def test_prever_neutral_symmetry_real_model(t1: str, t2: str) -> None:
    """Com o modelo real e ELOs da Copa 2026, a ordem nao deve alterar P(t1 vence)."""
    from components.data_loader import load_matches, compute_elo, train_models
    matches_raw = load_matches()
    matches, elo_ratings, _ = compute_elo(matches_raw)
    model, *_ = train_models(matches)

    e1, e2 = elo_ratings[t1], elo_ratings[t2]
    ph, pd, pa = _prever_neutral(model, e1, e2)
    qh, qd, qa = _prever_neutral(model, e2, e1)

    assert abs(ph - qa) < 1e-10, f"{t1}x{t2}: P({t1} vence) home={ph:.6f} away={qa:.6f}"
    assert abs(pd - qd) < 1e-10, f"{t1}x{t2}: P(empate) {pd:.6f} vs {qd:.6f}"
    assert abs(ph + pd + pa - 1.0) < 1e-6  # float32: epsilon ~1.2e-7

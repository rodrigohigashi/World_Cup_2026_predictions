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


# ── Testes de phase_idx ───────────────────────────────────────────────────────

@pytest.mark.parametrize("bracket_size,expected_start", [
    (16, 0),  # R16 → começa em "quartas"
    (8,  1),  # QF  → começa em "semi"
    (4,  2),  # SF  → começa em "final"
    (2,  3),  # Final → champion branch dispara na 1ª rodada de qualquer forma
])
def test_phase_idx_start_formula(bracket_size: int, expected_start: int) -> None:
    """A fórmula max(0, 5 - bit_length) deve alinhar ao estagio atual do torneio."""
    assert max(0, 5 - bracket_size.bit_length()) == expected_start


def test_phase_idx_nao_produz_final_zero_para_bracket_size_4() -> None:
    """
    Com 4 times (SF, bracket_size=4), os 2 vencedores da rodada 1 devem ser
    contados em 'final', nao em 'quartas'. Antes da correcao, 'final' ficava 0.0%.
    """
    from itertools import combinations as _comb
    from components.data_loader import _make_bracket, _simular_jogo, _BYE, _prever_neutral

    class _FairModel:
        def predict_proba(self, X):
            return np.array([[0.40, 0.20, 0.40]])

    teams = ["A", "B", "C", "D"]
    bracket_size = 4
    n_byes = 0
    model = _FairModel()
    elos = {t: 1500.0 for t in teams}

    prob_cache = {}
    for t1, t2 in _comb(teams, 2):
        ph, pd_, pa = _prever_neutral(model, elos[t1], elos[t2])
        prob_cache[(t1, t2)] = (ph, pd_, pa)
        prob_cache[(t2, t1)] = (pa, pd_, ph)

    phases = ["quartas", "semi", "final", "campeao"]
    counts = {t: {p: 0 for p in phases} for t in teams}

    np.random.seed(0)
    N = 5_000
    for _ in range(N):
        bracket = _make_bracket(teams, n_byes, bracket_size)
        phase_idx = max(0, 5 - bracket_size.bit_length())  # deve ser 2 → "final"
        while len(bracket) > 1:
            proxima = []
            for i in range(0, len(bracket), 2):
                h, a = bracket[i], bracket[i + 1]
                ph, pd2, pa = prob_cache[(h, a)]
                venc = h if _simular_jogo(ph, pd2, pa) == "home" else a
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

    for t in teams:
        p_quartas = counts[t]["quartas"] / N
        p_semi    = counts[t]["semi"]    / N
        p_final   = counts[t]["final"]   / N
        p_campeao = counts[t]["campeao"] / N

        assert p_quartas == 0.0, f"quartas deveria ser 0 para bracket_size=4, mas {t}={p_quartas:.3f}"
        assert p_semi    == 0.0, f"semi deveria ser 0 para bracket_size=4, mas {t}={p_semi:.3f}"
        assert abs(p_final   - 0.5)  < 0.05, f"final esperado ~50%, obtido {p_final:.3f}"
        assert abs(p_campeao - 0.25) < 0.05, f"campeao esperado ~25%, obtido {p_campeao:.3f}"

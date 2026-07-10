"""
Testes para _make_bracket em data_loader.py.

Duas propriedades verificadas:
1. Nenhum par adjacente e BYE x BYE (previne o KeyError original).
2. Cada time tem exatamente P = n_byes/n_alive de receber BYE (uniformidade).

Se alguem reverter para o shuffle ingenuo (teams + [BYE]*n_byes), o teste
n_alive=6 falha em ambas as propriedades.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np
import pytest

from components.data_loader import _BYE, _make_bracket


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

"""
Verifica que _make_bracket nunca produz um par BYE x BYE.

Se alguém reverter a correcao estrutural em data_loader.py e voltar ao
shuffle ingenuo (teams + [BYE]*n_byes), o caso n_alive=6 falha imediatamente.
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

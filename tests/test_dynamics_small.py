import sys
from pathlib import Path

import numpy as np
from scipy import sparse


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from rccn_persistence.dynamics import update_spins_once


def test_update_spins_once_matches_manual_calculation():
    J = sparse.csr_matrix(
        np.array(
            [
                [0.0, 1.0, 0.0],
                [0.0, 0.0, -1.0],
                [1.0, 0.0, 0.0],
            ]
        )
    )
    spins = np.array([1.0, -1.0, 1.0])
    new_spins, zero_count = update_spins_once(spins, J, H=0.2)
    np.testing.assert_array_equal(new_spins, np.array([-1.0, -1.0, 1.0]))
    assert zero_count == 0


def test_zero_field_keeps_previous_spin():
    J = sparse.csr_matrix((2, 2))
    spins = np.array([1.0, -1.0])
    new_spins, zero_count = update_spins_once(spins, J, H=0.0)
    np.testing.assert_array_equal(new_spins, spins)
    assert zero_count == 2


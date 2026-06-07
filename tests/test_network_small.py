import sys
from pathlib import Path

import numpy as np
from scipy import sparse


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from rccn_persistence.network import build_shift_edges, sample_cycle_lengths


def test_cycle_lengths_cover_all_spins():
    rng = np.random.default_rng(1)
    cycle_lengths = sample_cycle_lengths(100, 20, rng)
    assert cycle_lengths.sum() == 100


def test_shift_edges_for_one_cycle_matches_matlab_gen_shift_mat():
    rows, cols, values = build_shift_edges(np.array([0]), np.array([4]))
    J = sparse.csr_matrix((values, (rows, cols)), shape=(4, 4))
    spins = np.array([1.0, -1.0, -1.0, 1.0])
    np.testing.assert_array_equal(J @ spins, np.array([-1.0, -1.0, 1.0, 1.0]))


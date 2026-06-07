import sys
from pathlib import Path

import numpy as np


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from rccn_persistence.observables import (
    compute_global_magnetization,
    compute_recovery_time,
)


def test_cycle_averaged_magnetization():
    spins = np.array([1.0, -1.0, 1.0, 1.0, -1.0, -1.0])
    cycle_starts = np.array([0, 2])
    cycle_lengths = np.array([2, 4])
    observed = compute_global_magnetization(spins, cycle_starts, cycle_lengths)
    expected = ((1 - 1) / 2 + (1 + 1 - 1 - 1) / 4) / 2
    assert observed == expected


def test_recovery_time_first_crossing_uses_strictly_below_baseline():
    mag = np.array([0.1, 0.2, 0.2, 0.9, 0.8, 0.2, 0.19, 0.18])
    recovery_time, recovered, baseline = compute_recovery_time(
        mag, init_time=3, Tw=2, baseline_window=2
    )
    assert baseline == 0.2
    assert recovery_time == 1
    assert recovered is True


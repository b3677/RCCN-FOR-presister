import sys
from pathlib import Path

import numpy as np
import pandas as pd


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from rccn_persistence.observables import (
    classify_cell_fate,
    compute_global_magnetization,
    compute_recovery_time,
    compute_recovery_survival_to_zero_by_Tw,
    summarize_fate_by_Tw,
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


def test_cell_fate_uses_censoring_or_recovery_threshold():
    metadata = pd.DataFrame(
        {
            "run_id": [0, 1, 2],
            "Tw": [20, 20, 40],
            "recovered": [True, False, True],
            "recovery_time": [10.0, np.nan, 200.0],
        }
    )

    default_fate = classify_cell_fate(metadata)
    assert default_fate["fate"].tolist() == ["regrowth", "persister", "regrowth"]

    threshold_fate = classify_cell_fate(metadata, persister_recovery_time=100)
    assert threshold_fate["fate"].tolist() == ["regrowth", "persister", "persister"]

    summary = summarize_fate_by_Tw(metadata)
    assert set(summary["fate"]) == {"regrowth", "persister"}


def test_recovery_survival_to_zero_uses_first_m_less_than_or_equal_zero(tmp_path):
    magnetization = pd.DataFrame(
        {
            "run_id": [0, 0, 0, 1, 1, 1],
            "Tw": [0, 0, 0, 0, 0, 0],
            "time": [5, 6, 7, 5, 6, 7],
            "magnetization": [0.2, 0.0, -0.1, 0.3, 0.2, -0.2],
        }
    )
    path = tmp_path / "magnetization.csv"
    magnetization.to_csv(path, index=False)
    metadata = pd.DataFrame(
        {
            "run_id": [0, 1],
            "Tw": [0, 0],
            "snapshot_time": [5, 5],
        }
    )

    survival = compute_recovery_survival_to_zero_by_Tw(
        path, metadata, max_time=2, chunksize=2
    )

    assert survival["survival"].tolist() == [1.0, 0.5, 0.0]
    assert survival["n_recovered_by_time"].tolist() == [0, 1, 2]

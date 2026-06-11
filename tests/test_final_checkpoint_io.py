import sys
from pathlib import Path

import numpy as np
import pandas as pd


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from rccn_persistence.io_utils import (
    is_waiting_time_checkpoint_complete,
    load_waiting_time_checkpoint,
    save_waiting_time_checkpoint,
)
from rccn_persistence.simulation import make_run_seed, merge_waiting_time_results


def make_params(n_runs=2):
    return {
        "n_runs": n_runs,
        "num_spins": 4,
        "init_time": 20,
        "relax_time": 120,
        "gamma": 1.5,
        "H_init": 0.0,
        "H_stress": 0.8,
        "H_relax": 0.0,
        "max_cycle_length": 10,
        "selected_recovery_times": [0, 10],
        "random_seed": 1,
    }


def make_waiting_time_result(Tw, run_id_start=0):
    run_ids = [run_id_start, run_id_start + 1]
    return {
        "metadata": pd.DataFrame(
            {
                "run_id": run_ids,
                "Tw": [Tw, Tw],
                "recovery_time": [1.0, 2.0],
            }
        ),
        "magnetization": pd.DataFrame(
            {
                "run_id": [run_ids[0], run_ids[0], run_ids[1], run_ids[1]],
                "Tw": [Tw, Tw, Tw, Tw],
                "time": [0, 1, 0, 1],
                "magnetization": [0.1, 0.2, 0.3, 0.4],
            }
        ),
        "spin_release": np.ones((2, 4)),
        "spin_early_recovery": np.zeros((2, 4)),
        "selected_spin_snapshots": np.arange(16).reshape(4, 4),
        "snapshot_metadata": pd.DataFrame(
            {
                "run_id": [run_ids[0], run_ids[0], run_ids[1], run_ids[1]],
                "Tw": [Tw, Tw, Tw, Tw],
                "state_recovery_time": [0, 10, 0, 10],
            }
        ),
        "cycle_group_features": pd.DataFrame(
            {
                "run_id": [run_ids[0], run_ids[1]],
                "Tw": [Tw, Tw],
                "state_recovery_time": [0, 0],
                "cycle_mean_magnetization": [0.5, 0.6],
            }
        ),
    }


def test_waiting_time_checkpoint_round_trip(tmp_path):
    params = make_params()
    result = make_waiting_time_result(Tw=195)

    save_waiting_time_checkpoint(result, tmp_path, Tw=195, params=params, worker_count=2)

    assert is_waiting_time_checkpoint_complete(tmp_path, Tw=195, params=params)
    loaded = load_waiting_time_checkpoint(tmp_path, Tw=195)
    assert list(loaded.keys()) == list(result.keys())
    assert loaded["metadata"].shape == result["metadata"].shape
    np.testing.assert_array_equal(loaded["spin_release"], result["spin_release"])


def test_checkpoint_rejects_parameter_mismatch(tmp_path):
    params = make_params()
    result = make_waiting_time_result(Tw=488)
    save_waiting_time_checkpoint(result, tmp_path, Tw=488, params=params)

    changed_params = make_params()
    changed_params["num_spins"] = 8

    assert not is_waiting_time_checkpoint_complete(
        tmp_path, Tw=488, params=changed_params
    )


def test_merge_waiting_time_results_preserves_tables_and_matrices():
    first = make_waiting_time_result(Tw=0, run_id_start=0)
    second = make_waiting_time_result(Tw=195, run_id_start=2)

    merged = merge_waiting_time_results([first, second])

    assert merged["metadata"]["Tw"].tolist() == [0, 0, 195, 195]
    assert merged["spin_release"].shape == (4, 4)
    assert merged["selected_spin_snapshots"].shape == (8, 4)


def test_make_run_seed_is_stable_and_run_specific():
    seed_a = make_run_seed(base_seed=1, Tw=195, run_id=3)
    seed_b = make_run_seed(base_seed=1, Tw=195, run_id=3)
    seed_c = make_run_seed(base_seed=1, Tw=195, run_id=4)

    assert seed_a == seed_b
    assert seed_a != seed_c

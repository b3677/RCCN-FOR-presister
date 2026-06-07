import numpy as np
import pandas as pd

from .dynamics import run_one_protocol
from .network import build_rccn_network
from .observables import compute_recovery_time


def run_one_cell(params, Tw, run_id, rng):
    network = build_rccn_network(params, rng)
    protocol_result = run_one_protocol(network, params, Tw, rng)
    mag = protocol_result["magnetization"]["magnetization"].to_numpy()
    recovery_time, recovered, baseline_magnetization = compute_recovery_time(
        mag, params["init_time"], Tw, params["baseline_window"]
    )

    metadata = {
        "run_id": run_id,
        "Tw": Tw,
        "recovery_time": np.nan if recovery_time is None else recovery_time,
        "recovered": recovered,
        "baseline_magnetization": baseline_magnetization,
        "snapshot_time": params["init_time"] + Tw,
        "early_recovery_snapshot_time": params["init_time"]
        + Tw
        + params["early_recovery_delta"],
        "zero_field_count": protocol_result["zero_field_count"],
        "num_cycles": len(network["cycle_lengths"]),
    }

    magnetization = protocol_result["magnetization"].copy()
    magnetization.insert(0, "run_id", run_id)
    magnetization.insert(1, "Tw", Tw)

    return {
        "metadata": metadata,
        "magnetization": magnetization,
        "release_snapshot": protocol_result["release_snapshot"],
        "early_recovery_snapshot": protocol_result["early_recovery_snapshot"],
    }


def run_for_one_waiting_time(params, Tw, n_runs, rng, run_id_start=0):
    metadata_rows = []
    magnetization_tables = []
    release_snapshots = []
    early_snapshots = []

    for local_run in range(n_runs):
        run_id = run_id_start + local_run
        print(f"[simulate] Tw={Tw}, run={local_run + 1}/{n_runs}")
        result = run_one_cell(params, Tw, run_id, rng)
        metadata_rows.append(result["metadata"])
        magnetization_tables.append(result["magnetization"])
        release_snapshots.append(result["release_snapshot"])
        early_snapshots.append(result["early_recovery_snapshot"])

    return {
        "metadata": pd.DataFrame(metadata_rows),
        "magnetization": pd.concat(magnetization_tables, ignore_index=True),
        "spin_release": np.vstack(release_snapshots),
        "spin_early_recovery": np.vstack(early_snapshots),
    }


def run_batch(params):
    rng = np.random.default_rng(params["random_seed"])
    metadata_tables = []
    magnetization_tables = []
    release_matrices = []
    early_matrices = []
    next_run_id = 0

    for Tw in params["waiting_times"]:
        result = run_for_one_waiting_time(
            params, Tw, params["n_runs"], rng, run_id_start=next_run_id
        )
        metadata_tables.append(result["metadata"])
        magnetization_tables.append(result["magnetization"])
        release_matrices.append(result["spin_release"])
        early_matrices.append(result["spin_early_recovery"])
        next_run_id += params["n_runs"]

    return {
        "metadata": pd.concat(metadata_tables, ignore_index=True),
        "magnetization": pd.concat(magnetization_tables, ignore_index=True),
        "spin_release": np.vstack(release_matrices),
        "spin_early_recovery": np.vstack(early_matrices),
    }

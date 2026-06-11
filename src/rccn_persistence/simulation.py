from concurrent.futures import ProcessPoolExecutor, as_completed

import numpy as np
import pandas as pd

from .io_utils import (
    is_waiting_time_checkpoint_complete,
    load_waiting_time_checkpoint,
    save_waiting_time_checkpoint,
)
from .dynamics import run_one_protocol
from .network import build_rccn_network
from .observables import compute_cycle_group_features, compute_recovery_time


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

    selected_snapshot_rows = []
    snapshot_metadata_rows = []
    cycle_group_rows = []
    for state_recovery_time in params.get("selected_recovery_times", [0]):
        state_recovery_time = int(state_recovery_time)
        snapshot = protocol_result["selected_snapshots"][state_recovery_time]
        selected_snapshot_rows.append(snapshot)
        snapshot_metadata_rows.append(
            {
                "run_id": run_id,
                "Tw": Tw,
                "state_recovery_time": state_recovery_time,
                "absolute_snapshot_time": params["init_time"]
                + Tw
                + state_recovery_time,
            }
        )
        cycle_row = {
            "run_id": run_id,
            "Tw": Tw,
            "state_recovery_time": state_recovery_time,
        }
        cycle_row.update(
            compute_cycle_group_features(
                snapshot, network["cycle_starts"], network["cycle_lengths"]
            )
        )
        cycle_group_rows.append(cycle_row)

    return {
        "metadata": metadata,
        "magnetization": magnetization,
        "release_snapshot": protocol_result["release_snapshot"],
        "early_recovery_snapshot": protocol_result["early_recovery_snapshot"],
        "selected_spin_snapshots": np.vstack(selected_snapshot_rows),
        "snapshot_metadata": pd.DataFrame(snapshot_metadata_rows),
        "cycle_group_features": pd.DataFrame(cycle_group_rows),
    }


def run_for_one_waiting_time(params, Tw, n_runs, rng, run_id_start=0):
    metadata_rows = []
    magnetization_tables = []
    release_snapshots = []
    early_snapshots = []
    selected_snapshot_matrices = []
    snapshot_metadata_tables = []
    cycle_group_tables = []

    for local_run in range(n_runs):
        run_id = run_id_start + local_run
        print(f"[simulate] Tw={Tw}, run={local_run + 1}/{n_runs}")
        result = run_one_cell(params, Tw, run_id, rng)
        metadata_rows.append(result["metadata"])
        magnetization_tables.append(result["magnetization"])
        release_snapshots.append(result["release_snapshot"])
        early_snapshots.append(result["early_recovery_snapshot"])
        selected_snapshot_matrices.append(result["selected_spin_snapshots"])
        snapshot_metadata_tables.append(result["snapshot_metadata"])
        cycle_group_tables.append(result["cycle_group_features"])

    return {
        "metadata": pd.DataFrame(metadata_rows),
        "magnetization": pd.concat(magnetization_tables, ignore_index=True),
        "spin_release": np.vstack(release_snapshots),
        "spin_early_recovery": np.vstack(early_snapshots),
        "selected_spin_snapshots": np.vstack(selected_snapshot_matrices),
        "snapshot_metadata": pd.concat(snapshot_metadata_tables, ignore_index=True),
        "cycle_group_features": pd.concat(cycle_group_tables, ignore_index=True),
    }


def make_run_seed(base_seed, Tw, run_id):
    seed_sequence = np.random.SeedSequence([int(base_seed), int(Tw), int(run_id)])
    return int(seed_sequence.generate_state(1, dtype=np.uint32)[0])


def run_one_cell_from_seed(params, Tw, run_id, seed):
    rng = np.random.default_rng(seed)
    return run_one_cell(params, Tw, run_id, rng)


def _combine_cell_results(cell_results):
    return {
        "metadata": pd.DataFrame([result["metadata"] for result in cell_results]),
        "magnetization": pd.concat(
            [result["magnetization"] for result in cell_results],
            ignore_index=True,
        ),
        "spin_release": np.vstack(
            [result["release_snapshot"] for result in cell_results]
        ),
        "spin_early_recovery": np.vstack(
            [result["early_recovery_snapshot"] for result in cell_results]
        ),
        "selected_spin_snapshots": np.vstack(
            [result["selected_spin_snapshots"] for result in cell_results]
        ),
        "snapshot_metadata": pd.concat(
            [result["snapshot_metadata"] for result in cell_results],
            ignore_index=True,
        ),
        "cycle_group_features": pd.concat(
            [result["cycle_group_features"] for result in cell_results],
            ignore_index=True,
        ),
    }


def run_for_one_waiting_time_parallel(params, Tw, n_runs, run_id_start=0, workers=1):
    tasks = []
    for local_run in range(n_runs):
        run_id = run_id_start + local_run
        seed = make_run_seed(params["random_seed"], Tw, run_id)
        tasks.append((params, Tw, run_id, seed))

    if workers <= 1:
        cell_results = []
        for local_run, (task_params, task_Tw, run_id, seed) in enumerate(tasks):
            print(f"[simulate] Tw={Tw}, run={local_run + 1}/{n_runs}")
            cell_results.append(
                run_one_cell_from_seed(task_params, task_Tw, run_id, seed)
            )
        return _combine_cell_results(cell_results)

    cell_results = []
    completed = 0
    with ProcessPoolExecutor(max_workers=workers) as executor:
        futures = [
            executor.submit(run_one_cell_from_seed, task_params, task_Tw, run_id, seed)
            for task_params, task_Tw, run_id, seed in tasks
        ]
        for future in as_completed(futures):
            cell_results.append(future.result())
            completed += 1
            print(f"[simulate] Tw={Tw}, done={completed}/{n_runs}")

    cell_results.sort(key=lambda result: result["metadata"]["run_id"])
    return _combine_cell_results(cell_results)


def merge_waiting_time_results(waiting_time_results):
    return {
        "metadata": pd.concat(
            [result["metadata"] for result in waiting_time_results],
            ignore_index=True,
        ),
        "magnetization": pd.concat(
            [result["magnetization"] for result in waiting_time_results],
            ignore_index=True,
        ),
        "spin_release": np.vstack(
            [result["spin_release"] for result in waiting_time_results]
        ),
        "spin_early_recovery": np.vstack(
            [result["spin_early_recovery"] for result in waiting_time_results]
        ),
        "selected_spin_snapshots": np.vstack(
            [result["selected_spin_snapshots"] for result in waiting_time_results]
        ),
        "snapshot_metadata": pd.concat(
            [result["snapshot_metadata"] for result in waiting_time_results],
            ignore_index=True,
        ),
        "cycle_group_features": pd.concat(
            [result["cycle_group_features"] for result in waiting_time_results],
            ignore_index=True,
        ),
    }


def run_batch_with_tw_checkpoints(params, checkpoint_root, workers=1, resume=True):
    next_run_id = 0

    for Tw in params["waiting_times"]:
        if resume and is_waiting_time_checkpoint_complete(checkpoint_root, Tw, params):
            print(f"[resume] found complete Tw={Tw} checkpoint")
        else:
            result = run_for_one_waiting_time_parallel(
                params=params,
                Tw=Tw,
                n_runs=params["n_runs"],
                run_id_start=next_run_id,
                workers=workers,
            )
            save_waiting_time_checkpoint(
                result,
                checkpoint_root,
                Tw,
                params,
                worker_count=workers,
            )
            print(f"[checkpoint] saved Tw={Tw}")
            del result

        next_run_id += params["n_runs"]

    waiting_time_results = [
        load_waiting_time_checkpoint(checkpoint_root, Tw)
        for Tw in params["waiting_times"]
    ]
    return merge_waiting_time_results(waiting_time_results)


def run_batch(params):
    rng = np.random.default_rng(params["random_seed"])
    metadata_tables = []
    magnetization_tables = []
    release_matrices = []
    early_matrices = []
    selected_snapshot_matrices = []
    snapshot_metadata_tables = []
    cycle_group_tables = []
    next_run_id = 0

    for Tw in params["waiting_times"]:
        result = run_for_one_waiting_time(
            params, Tw, params["n_runs"], rng, run_id_start=next_run_id
        )
        metadata_tables.append(result["metadata"])
        magnetization_tables.append(result["magnetization"])
        release_matrices.append(result["spin_release"])
        early_matrices.append(result["spin_early_recovery"])
        selected_snapshot_matrices.append(result["selected_spin_snapshots"])
        snapshot_metadata_tables.append(result["snapshot_metadata"])
        cycle_group_tables.append(result["cycle_group_features"])
        next_run_id += params["n_runs"]

    return {
        "metadata": pd.concat(metadata_tables, ignore_index=True),
        "magnetization": pd.concat(magnetization_tables, ignore_index=True),
        "spin_release": np.vstack(release_matrices),
        "spin_early_recovery": np.vstack(early_matrices),
        "selected_spin_snapshots": np.vstack(selected_snapshot_matrices),
        "snapshot_metadata": pd.concat(snapshot_metadata_tables, ignore_index=True),
        "cycle_group_features": pd.concat(cycle_group_tables, ignore_index=True),
    }

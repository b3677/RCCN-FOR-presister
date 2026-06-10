import numpy as np
import pandas as pd

from .observables import compute_global_magnetization


def initialize_spins(num_spins, rng):
    return np.where(rng.random(num_spins) < 0.5, 1.0, -1.0)


def sign_without_zero_problem(local_field, previous_spins):
    new_spins = np.empty_like(previous_spins)
    new_spins[local_field > 0] = 1.0
    new_spins[local_field < 0] = -1.0
    zero_mask = local_field == 0
    new_spins[zero_mask] = previous_spins[zero_mask]
    return new_spins, int(np.count_nonzero(zero_mask))


def update_spins_once(spins, J, H):
    local_field = J @ spins + H
    return sign_without_zero_problem(local_field, spins)


def run_one_protocol(network, params, Tw, rng):
    spins = initialize_spins(params["num_spins"], rng)
    J = network["J"]
    cycle_starts = network["cycle_starts"]
    cycle_lengths = network["cycle_lengths"]

    release_time = params["init_time"] + Tw
    early_time = release_time + params["early_recovery_delta"]
    selected_recovery_times = params.get("selected_recovery_times", [0])
    selected_snapshot_times = {
        release_time + int(recovery_time): int(recovery_time)
        for recovery_time in selected_recovery_times
    }
    total_time = release_time + params["relax_time"]

    release_snapshot = None
    early_recovery_snapshot = None
    selected_snapshots = {}
    zero_field_count = 0
    mag_rows = []

    for time in range(total_time):
        if time == release_time:
            release_snapshot = spins.copy()
        if time == early_time:
            early_recovery_snapshot = spins.copy()
        if time in selected_snapshot_times:
            recovery_time = selected_snapshot_times[time]
            selected_snapshots[recovery_time] = spins.copy()

        mag_rows.append(
            {
                "time": time,
                "magnetization": compute_global_magnetization(
                    spins, cycle_starts, cycle_lengths
                ),
            }
        )

        if time < params["init_time"]:
            H = params["H_init"]
        elif time < release_time:
            H = params["H_stress"]
        else:
            H = params["H_relax"]

        spins, zero_count = update_spins_once(spins, J, H)
        zero_field_count += zero_count

    if release_snapshot is None:
        raise RuntimeError("release snapshot was not recorded")
    if early_recovery_snapshot is None:
        raise RuntimeError("early recovery snapshot was not recorded")
    missing = [
        recovery_time
        for recovery_time in selected_recovery_times
        if int(recovery_time) not in selected_snapshots
    ]
    if missing:
        raise RuntimeError(f"selected recovery snapshots were not recorded: {missing}")

    return {
        "magnetization": pd.DataFrame(mag_rows),
        "release_snapshot": release_snapshot,
        "early_recovery_snapshot": early_recovery_snapshot,
        "selected_snapshots": selected_snapshots,
        "final_spins": spins,
        "zero_field_count": zero_field_count,
    }

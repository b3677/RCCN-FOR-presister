import numpy as np
import pandas as pd


def compute_cycle_magnetization(spins, cycle_starts, cycle_lengths):
    cycle_sums = np.add.reduceat(spins, cycle_starts)
    return cycle_sums / cycle_lengths


def compute_global_magnetization(spins, cycle_starts, cycle_lengths):
    cycle_mags = compute_cycle_magnetization(spins, cycle_starts, cycle_lengths)
    return float(np.mean(cycle_mags))


def compute_baseline_magnetization(mag, init_time, baseline_window=1000):
    start = max(0, init_time - baseline_window)
    return float(np.mean(np.asarray(mag)[start:init_time]))


def compute_recovery_time(mag, init_time, Tw, baseline_window=1000):
    mag = np.asarray(mag)
    m_base = compute_baseline_magnetization(mag, init_time, baseline_window)
    release_index = init_time + Tw
    relaxation = mag[release_index:] - m_base
    crossing = np.flatnonzero(relaxation < 0)

    if len(crossing) == 0:
        return None, False, m_base

    return int(crossing[0]), True, m_base


def compute_recovery_cdf(recovery_times, max_time):
    recovery_times = pd.Series(recovery_times).dropna().to_numpy()
    time_grid = np.arange(1, max_time + 1)

    if len(recovery_times) == 0:
        cdf = np.zeros_like(time_grid, dtype=float)
    else:
        cdf = np.array([(recovery_times <= t).mean() for t in time_grid])

    return pd.DataFrame({"time": time_grid, "cdf": cdf})


def compute_survival_curve(recovery_times, max_time):
    cdf = compute_recovery_cdf(recovery_times, max_time)
    cdf["survival"] = 1.0 - cdf["cdf"]
    return cdf[["time", "survival", "cdf"]]


def compute_survival_by_Tw(metadata, max_time):
    tables = []
    for Tw, group in metadata.groupby("Tw"):
        table = compute_survival_curve(group["recovery_time"], max_time)
        table.insert(0, "Tw", Tw)
        tables.append(table)
    return pd.concat(tables, ignore_index=True)


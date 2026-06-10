import numpy as np
import pandas as pd


def compute_cycle_magnetization(spins, cycle_starts, cycle_lengths):
    cycle_sums = np.add.reduceat(spins, cycle_starts)
    return cycle_sums / cycle_lengths


def compute_global_magnetization(spins, cycle_starts, cycle_lengths):
    cycle_mags = compute_cycle_magnetization(spins, cycle_starts, cycle_lengths)
    return float(np.mean(cycle_mags))


def compute_cycle_group_features(spins, cycle_starts, cycle_lengths):
    """Summarize one cell by short/medium/long cycle magnetization."""
    cycle_mags = compute_cycle_magnetization(spins, cycle_starts, cycle_lengths)
    cycle_lengths = np.asarray(cycle_lengths)
    if len(cycle_lengths) < 3:
        short_cut = np.quantile(cycle_lengths, 1 / 3)
        long_cut = np.quantile(cycle_lengths, 2 / 3)
    else:
        short_cut, long_cut = np.quantile(cycle_lengths, [1 / 3, 2 / 3])

    groups = {
        "short": cycle_lengths <= short_cut,
        "medium": (cycle_lengths > short_cut) & (cycle_lengths <= long_cut),
        "long": cycle_lengths > long_cut,
    }
    row = {}
    for name, mask in groups.items():
        if np.any(mask):
            row[f"{name}_cycle_activation"] = float(np.mean(cycle_mags[mask]))
            row[f"n_{name}_cycles"] = int(np.count_nonzero(mask))
        else:
            row[f"{name}_cycle_activation"] = np.nan
            row[f"n_{name}_cycles"] = 0
    return row


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


def classify_cell_fate(metadata, persister_recovery_time=None):
    """Label simulated cells as regrowth or persister-like."""
    metadata = metadata.copy()
    recovered = metadata["recovered"].astype(bool)

    if persister_recovery_time is None:
        is_persister = ~recovered
    else:
        recovery_time = pd.to_numeric(metadata["recovery_time"], errors="coerce")
        is_persister = (~recovered) | (recovery_time >= persister_recovery_time)

    metadata["fate"] = np.where(is_persister, "persister", "regrowth")
    return metadata


def summarize_fate_by_Tw(metadata, persister_recovery_time=None):
    metadata_with_fate = classify_cell_fate(metadata, persister_recovery_time)
    counts = (
        metadata_with_fate.groupby(["Tw", "fate"])
        .size()
        .rename("count")
        .reset_index()
    )
    counts["fraction"] = counts["count"] / counts.groupby("Tw")["count"].transform("sum")
    return counts


def compute_recovery_dynamics_by_Tw(magnetization, metadata):
    release_times = metadata[["run_id", "snapshot_time"]].copy()
    merged = magnetization.merge(release_times, on="run_id")
    merged["recovery_time"] = merged["time"] - merged["snapshot_time"]
    merged = merged[merged["recovery_time"] >= 0].copy()
    summary = (
        merged.groupby(["Tw", "recovery_time"])["magnetization"]
        .agg(["mean", "std", "count"])
        .reset_index()
    )
    summary = summary.rename(
        columns={
            "mean": "mean_recovery_observable",
            "std": "std_recovery_observable",
            "count": "n_simulations",
        }
    )
    summary["sem_recovery_observable"] = (
        summary["std_recovery_observable"] / np.sqrt(summary["n_simulations"])
    )
    return summary[
        [
            "Tw",
            "recovery_time",
            "mean_recovery_observable",
            "std_recovery_observable",
            "sem_recovery_observable",
            "n_simulations",
        ]
    ].sort_values(["Tw", "recovery_time"])


def extrapolate_tail_fraction(source_table, target_Tw):
    table = source_table.sort_values("Tw")
    x = table["Tw"].to_numpy(dtype=float)
    y = table["TailFraction"].to_numpy(dtype=float)
    y_std = table["TailFractionSTD"].to_numpy(dtype=float)
    tail_fraction = float(np.interp(target_Tw, x, y))
    tail_std = float(np.interp(target_Tw, x, y_std))

    if target_Tw > x.max() and len(x) >= 2:
        slope = (y[-1] - y[-2]) / (x[-1] - x[-2])
        std_slope = (y_std[-1] - y_std[-2]) / (x[-1] - x[-2])
        tail_fraction = float(y[-1] + slope * (target_Tw - x[-1]))
        tail_std = float(y_std[-1] + std_slope * (target_Tw - x[-1]))
    elif target_Tw < x.min() and len(x) >= 2:
        slope = (y[1] - y[0]) / (x[1] - x[0])
        std_slope = (y_std[1] - y_std[0]) / (x[1] - x[0])
        tail_fraction = float(y[0] + slope * (target_Tw - x[0]))
        tail_std = float(y_std[0] + std_slope * (target_Tw - x[0]))

    return max(0.0, min(1.0, tail_fraction)), max(0.0, tail_std)


def load_tail_fraction_table(sourcefig2_path, target_waiting_times):
    source = pd.read_excel(sourcefig2_path, sheet_name="Fig2c")
    required = {"Tw_minutes", "TailFraction", "TailFractionSTD"}
    missing = required - set(source.columns)
    if missing:
        raise ValueError(f"sourcefig2 Fig2c is missing columns: {sorted(missing)}")

    source = source.rename(columns={"Tw_minutes": "Tw"})
    source = source[["Tw", "TailFraction", "TailFractionSTD"]].dropna()
    rows = []
    for Tw in target_waiting_times:
        direct = source[source["Tw"] == Tw]
        if not direct.empty:
            row = direct.iloc[0]
            rows.append(
                {
                    "Tw": Tw,
                    "TailFraction": float(row["TailFraction"]),
                    "TailFractionSTD": float(row["TailFractionSTD"]),
                    "TailFraction_source": "sourcefig2_direct",
                }
            )
        else:
            value, std = extrapolate_tail_fraction(source, Tw)
            rows.append(
                {
                    "Tw": Tw,
                    "TailFraction": value,
                    "TailFractionSTD": std,
                    "TailFraction_source": "sourcefig2_extrapolated",
                }
            )
    return pd.DataFrame(rows)


def assign_presister_like_by_tail_fraction(metadata, tail_fraction_table):
    labeled = metadata.copy()
    labeled["presister_like"] = False
    recovery = pd.to_numeric(labeled["recovery_time"], errors="coerce")
    slow_rank_value = recovery.fillna(np.inf)

    for Tw, group in labeled.groupby("Tw"):
        tail_row = tail_fraction_table[tail_fraction_table["Tw"] == Tw]
        if tail_row.empty:
            raise ValueError(f"missing TailFraction for Tw={Tw}")
        tail_fraction = float(tail_row.iloc[0]["TailFraction"])
        n_presister = int(np.ceil(len(group) * tail_fraction))
        if n_presister == 0:
            continue
        group_rank = slow_rank_value.loc[group.index].sort_values(ascending=False)
        presister_index = group_rank.index[:n_presister]
        labeled.loc[presister_index, "presister_like"] = True

    labeled["state_label"] = np.where(
        labeled["presister_like"], "presister-like", "normal"
    )
    return labeled


def summarize_cluster_by_Tw(cell_state_table, state_recovery_time_for_summary=0):
    table = cell_state_table[
        cell_state_table["state_recovery_time"] == state_recovery_time_for_summary
    ].copy()
    grouped = table.groupby(["Tw", "cluster_id"])
    summary = (
        grouped.agg(
            n_cells=("run_id", "count"),
            mean_lag_time=("lag_time", "mean"),
            median_lag_time=("lag_time", "median"),
            presister_like_fraction=("presister_like", "mean"),
            mean_PC1=("PC1", "mean"),
            mean_PC2=("PC2", "mean"),
        )
        .reset_index()
        .rename(columns={"cluster_id": "cluster_id"})
    )
    summary["cluster_fraction"] = summary["n_cells"] / summary.groupby("Tw")[
        "n_cells"
    ].transform("sum")
    return summary.sort_values(["Tw", "cluster_id"])

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from rccn_persistence.network import make_cycle_starts, sample_cycle_lengths
from rccn_persistence.observables import compute_cycle_magnetization
from rccn_persistence.simulation import make_run_seed


def parse_args():
    parser = argparse.ArgumentParser(
        description="Run extra RCCN analyses from existing result611 outputs."
    )
    parser.add_argument(
        "--simulation-dir",
        type=Path,
        default=PROJECT_ROOT / "output" / "result611" / "final_simulation",
    )
    parser.add_argument(
        "--analysis-dir",
        type=Path,
        default=PROJECT_ROOT / "output" / "result611" / "final_analysis",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=PROJECT_ROOT / "output" / "ex_analysis",
    )
    parser.add_argument(
        "--state-recovery-time",
        type=int,
        default=0,
        help="Snapshot time used for the main release-state analyses.",
    )
    parser.add_argument(
        "--k-values",
        type=int,
        nargs="+",
        default=[3, 4, 5, 6, 8, 10],
        help="KMeans cluster numbers to test on existing PC scores.",
    )
    parser.add_argument(
        "--window-size",
        type=int,
        default=100,
        help="Sliding-window size for loop-bin activity along PC1.",
    )
    parser.add_argument(
        "--tail-cluster",
        action="store_true",
        help="Run only tail-fraction cluster matching unless --loop-bins is also set.",
    )
    parser.add_argument(
        "--loop-bins",
        action="store_true",
        help="Run only refined loop-bin analysis unless --tail-cluster is also set.",
    )
    return parser.parse_args()


def ensure_dir(path):
    path.mkdir(parents=True, exist_ok=True)
    return path


def load_csv(path):
    print(f"[load] {path}")
    return pd.read_csv(path)


def pc_columns(table):
    columns = [col for col in table.columns if col.startswith("PC")]
    return sorted(columns, key=lambda col: int(col.replace("PC", "")))


def fit_log_linear_tail_fraction(tail_table, prediction_Tw):
    fit_table = tail_table[tail_table["TailFraction"] > 0].copy()
    x = fit_table["Tw"].to_numpy(dtype=float)
    y = np.log(fit_table["TailFraction"].to_numpy(dtype=float))
    slope, intercept = np.polyfit(x, y, deg=1)
    prediction_Tw = np.asarray(prediction_Tw, dtype=float)
    predicted = np.exp(intercept + slope * prediction_Tw)
    predicted = np.clip(predicted, 0.0, 1.0)
    return pd.DataFrame(
        {
            "Tw": prediction_Tw,
            "TailFraction_loglinear_fit": predicted,
            "fit_intercept": intercept,
            "fit_slope": slope,
        }
    )


def spearman_corr(x, y):
    x_rank = pd.Series(x).rank(method="average").to_numpy(dtype=float)
    y_rank = pd.Series(y).rank(method="average").to_numpy(dtype=float)
    if np.std(x_rank) == 0 or np.std(y_rank) == 0:
        return np.nan
    return float(np.corrcoef(x_rank, y_rank)[0, 1])


def cluster_scores_for_k(release_table, tail_table, k, random_seed):
    from sklearn.cluster import KMeans

    pcs = pc_columns(release_table)[:10]
    labels = KMeans(n_clusters=k, random_state=random_seed, n_init=20).fit_predict(
        release_table[pcs].to_numpy(dtype=float)
    )
    clustered = release_table.copy()
    clustered["extra_cluster_id"] = labels.astype(int)
    clustered["extra_k"] = int(k)

    fractions = (
        clustered.groupby(["extra_k", "Tw", "extra_cluster_id"])
        .agg(
            n_cells=("run_id", "count"),
            mean_lag_time=("lag_time", "mean"),
            median_lag_time=("lag_time", "median"),
            presister_like_fraction=("presister_like", "mean"),
            mean_PC1=("PC1", "mean"),
            mean_PC2=("PC2", "mean"),
            mean_UMAP1=("UMAP1", "mean"),
            mean_UMAP2=("UMAP2", "mean"),
        )
        .reset_index()
    )
    fractions["cluster_fraction"] = fractions["n_cells"] / fractions.groupby(
        ["extra_k", "Tw"]
    )["n_cells"].transform("sum")

    global_lag = release_table["lag_time"].mean()
    global_presister = release_table["presister_like"].mean()
    rows = []
    for cluster_id, group in fractions.groupby("extra_cluster_id"):
        merged = tail_table.merge(group, on="Tw", how="inner")
        if merged.empty:
            continue
        residual = merged["cluster_fraction"] - merged["TailFraction"]
        rmse = float(np.sqrt(np.mean(residual**2)))
        pearson = (
            float(np.corrcoef(merged["cluster_fraction"], merged["TailFraction"])[0, 1])
            if len(merged) > 1
            and merged["cluster_fraction"].std() > 0
            and merged["TailFraction"].std() > 0
            else np.nan
        )
        cluster_cells = clustered[clustered["extra_cluster_id"] == cluster_id]
        mean_lag = float(cluster_cells["lag_time"].mean())
        presister_fraction = float(cluster_cells["presister_like"].mean())
        rows.append(
            {
                "extra_k": int(k),
                "extra_cluster_id": int(cluster_id),
                "rmse_vs_tail_fraction": rmse,
                "mae_vs_tail_fraction": float(np.mean(np.abs(residual))),
                "pearson_vs_tail_fraction": pearson,
                "spearman_vs_tail_fraction": spearman_corr(
                    merged["cluster_fraction"], merged["TailFraction"]
                ),
                "mean_lag_time": mean_lag,
                "global_mean_lag_time": float(global_lag),
                "lag_time_enrichment": mean_lag / global_lag if global_lag else np.nan,
                "presister_like_fraction": presister_fraction,
                "global_presister_like_fraction": float(global_presister),
                "presister_like_enrichment": (
                    presister_fraction / global_presister if global_presister else np.nan
                ),
                "mean_cluster_fraction": float(merged["cluster_fraction"].mean()),
                "mean_tail_fraction": float(merged["TailFraction"].mean()),
                "n_tail_points_compared": int(len(merged)),
            }
        )

    return clustered, fractions, pd.DataFrame(rows)


def select_best_cluster(score_table):
    table = score_table.copy()
    table["biologically_enriched"] = (
        (table["lag_time_enrichment"] >= 1.0)
        | (table["presister_like_enrichment"] >= 1.0)
    )
    table = table.sort_values(
        [
            "biologically_enriched",
            "rmse_vs_tail_fraction",
            "spearman_vs_tail_fraction",
            "presister_like_enrichment",
        ],
        ascending=[False, True, False, False],
    )
    return table.iloc[0]


def plot_tail_fit(tail_table, fit_table, output_path):
    fig, ax = plt.subplots(figsize=(5.5, 4.0))
    ax.errorbar(
        tail_table["Tw"],
        tail_table["TailFraction"],
        yerr=tail_table.get("TailFractionSTD"),
        fmt="o",
        color="#2a6f97",
        ecolor="#8ecae6",
        capsize=3,
        label="experimental tail fraction",
    )
    ax.plot(
        fit_table["Tw"],
        fit_table["TailFraction_loglinear_fit"],
        color="#d62828",
        label="log-linear descriptive fit",
    )
    ax.set_xlabel("Tw")
    ax.set_ylabel("Tail fraction")
    ax.set_title("Experimental tail fraction vs Tw")
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(output_path, dpi=300)
    plt.close(fig)


def plot_best_cluster_fraction(fraction_table, tail_table, best, output_path):
    subset = fraction_table[
        (fraction_table["extra_k"] == int(best["extra_k"]))
        & (fraction_table["extra_cluster_id"] == int(best["extra_cluster_id"]))
    ].copy()
    merged = tail_table.merge(subset, on="Tw", how="inner")

    fig, ax = plt.subplots(figsize=(5.5, 4.0))
    ax.plot(
        merged["Tw"],
        merged["TailFraction"],
        marker="o",
        color="#2a6f97",
        label="tail fraction",
    )
    ax.plot(
        merged["Tw"],
        merged["cluster_fraction"],
        marker="s",
        color="#f77f00",
        label=f"K={int(best['extra_k'])}, cluster={int(best['extra_cluster_id'])}",
    )
    ax.set_xlabel("Tw")
    ax.set_ylabel("Fraction")
    ax.set_title("Best RCCN cluster fraction vs tail fraction")
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(output_path, dpi=300)
    plt.close(fig)


def plot_best_cluster_umap(clustered_table, best, output_path):
    subset = clustered_table[int(best["extra_k"])]
    is_best = subset["extra_cluster_id"] == int(best["extra_cluster_id"])
    fig, ax = plt.subplots(figsize=(5.2, 4.8))
    ax.scatter(
        subset.loc[~is_best, "UMAP1"],
        subset.loc[~is_best, "UMAP2"],
        s=8,
        c="#c7c7c7",
        alpha=0.45,
        linewidths=0,
    )
    ax.scatter(
        subset.loc[is_best, "UMAP1"],
        subset.loc[is_best, "UMAP2"],
        s=12,
        c="#d62828",
        alpha=0.8,
        linewidths=0,
    )
    ax.set_xlabel("UMAP1")
    ax.set_ylabel("UMAP2")
    ax.set_title(f"Best tail-matching cluster, K={int(best['extra_k'])}")
    fig.tight_layout()
    fig.savefig(output_path, dpi=300)
    plt.close(fig)


def plot_match_heatmap(score_table, output_path):
    pivot = score_table.pivot(
        index="extra_cluster_id", columns="extra_k", values="rmse_vs_tail_fraction"
    )
    fig, ax = plt.subplots(figsize=(6.0, 4.5))
    image = ax.imshow(pivot.to_numpy(dtype=float), aspect="auto", cmap="viridis_r")
    ax.set_xticks(np.arange(len(pivot.columns)))
    ax.set_xticklabels(pivot.columns)
    ax.set_yticks(np.arange(len(pivot.index)))
    ax.set_yticklabels(pivot.index)
    ax.set_xlabel("K")
    ax.set_ylabel("Cluster id")
    ax.set_title("RMSE vs experimental tail fraction")
    fig.colorbar(image, ax=ax, label="RMSE")
    fig.tight_layout()
    fig.savefig(output_path, dpi=300)
    plt.close(fig)


def run_tail_cluster_matching(args, params):
    output_dir = ensure_dir(args.output_dir / "tail_fraction_cluster_matching")
    cell_state = load_csv(args.analysis_dir / "cell_state_table.csv")
    tail_table = load_csv(args.analysis_dir / "tail_fraction_by_Tw.csv")
    release = cell_state[
        cell_state["state_recovery_time"] == args.state_recovery_time
    ].copy()
    release["presister_like"] = release["presister_like"].astype(bool)

    fit_grid = np.linspace(tail_table["Tw"].min(), tail_table["Tw"].max(), 200)
    tail_fit = fit_log_linear_tail_fraction(tail_table, fit_grid)
    tail_fit.to_csv(output_dir / "tail_fraction_fit.csv", index=False)
    plot_tail_fit(tail_table, tail_fit, output_dir / "tail_fraction_fit.png")

    clustered_by_k = {}
    fraction_tables = []
    score_tables = []
    for k in args.k_values:
        print(f"[tail-cluster] KMeans K={k}")
        clustered, fractions, scores = cluster_scores_for_k(
            release, tail_table, k, params.get("random_seed", 1)
        )
        clustered_by_k[int(k)] = clustered
        fraction_tables.append(fractions)
        score_tables.append(scores)

    all_fractions = pd.concat(fraction_tables, ignore_index=True)
    all_scores = pd.concat(score_tables, ignore_index=True)
    best = select_best_cluster(all_scores)

    all_fractions.to_csv(output_dir / "cluster_fraction_by_Tw_by_K.csv", index=False)
    all_scores.to_csv(output_dir / "cluster_match_scores.csv", index=False)

    best_cells = clustered_by_k[int(best["extra_k"])]
    best_cells = best_cells[
        best_cells["extra_cluster_id"] == int(best["extra_cluster_id"])
    ].copy()
    best_cells.to_csv(output_dir / "best_cluster_cell_summary.csv", index=False)

    plot_best_cluster_fraction(
        all_fractions,
        tail_table,
        best,
        output_dir / "best_cluster_fraction_vs_tail_fraction.png",
    )
    plot_best_cluster_umap(
        clustered_by_k, best, output_dir / "best_cluster_umap.png"
    )
    plot_match_heatmap(all_scores, output_dir / "cluster_match_score_heatmap.png")

    best.to_frame().T.to_csv(output_dir / "best_cluster_match.csv", index=False)
    print(
        "[tail-cluster] best match: "
        f"K={int(best['extra_k'])}, cluster={int(best['extra_cluster_id'])}, "
        f"RMSE={best['rmse_vs_tail_fraction']:.4g}"
    )


def quantile_bin_masks(cycle_lengths, n_bins=5):
    cycle_lengths = np.asarray(cycle_lengths)
    labels = pd.qcut(
        pd.Series(cycle_lengths),
        q=min(n_bins, len(cycle_lengths)),
        labels=False,
        duplicates="drop",
    )
    bins = []
    for bin_id in sorted(pd.Series(labels).dropna().unique()):
        mask = labels.to_numpy() == bin_id
        lengths = cycle_lengths[mask]
        bins.append(
            {
                "bin_type": "quantile",
                "bin_id": int(bin_id) + 1,
                "bin_label": f"Q{int(bin_id) + 1}",
                "mask": mask,
                "length_min": int(lengths.min()),
                "length_max": int(lengths.max()),
            }
        )
    return bins


def absolute_bin_masks(cycle_lengths):
    cycle_lengths = np.asarray(cycle_lengths)
    definitions = [
        (1, "1-5", 1, 5),
        (2, "6-20", 6, 20),
        (3, "21-100", 21, 100),
        (4, "101-500", 101, 500),
        (5, ">500", 501, np.inf),
    ]
    bins = []
    for bin_id, label, low, high in definitions:
        if np.isinf(high):
            mask = cycle_lengths >= low
        else:
            mask = (cycle_lengths >= low) & (cycle_lengths <= high)
        bins.append(
            {
                "bin_type": "absolute",
                "bin_id": bin_id,
                "bin_label": label,
                "mask": mask,
                "length_min": int(low),
                "length_max": np.nan if np.isinf(high) else int(high),
            }
        )
    return bins


def build_run_cycle_bins(params, metadata):
    by_run = {}
    for row in metadata[["run_id", "Tw"]].drop_duplicates().itertuples(index=False):
        seed = make_run_seed(params["random_seed"], int(row.Tw), int(row.run_id))
        rng = np.random.default_rng(seed)
        cycle_lengths = sample_cycle_lengths(
            params["num_spins"], params["max_cycle_length"], rng
        )
        cycle_starts = make_cycle_starts(cycle_lengths)
        by_run[int(row.run_id)] = {
            "cycle_starts": cycle_starts,
            "cycle_lengths": cycle_lengths,
            "bins": quantile_bin_masks(cycle_lengths)
            + absolute_bin_masks(cycle_lengths),
        }
    return by_run


def compute_loop_bin_activity(args, params):
    output_dir = ensure_dir(args.output_dir / "loop_length_bins")
    snapshot_metadata = load_csv(args.simulation_dir / "snapshot_metadata.csv")
    simulation_metadata = load_csv(args.simulation_dir / "metadata.csv")
    cell_state = load_csv(args.analysis_dir / "cell_state_table.csv")
    snapshots = np.load(args.simulation_dir / "selected_spin_snapshots.npy", mmap_mode="r")

    if len(snapshot_metadata) != snapshots.shape[0]:
        raise ValueError("snapshot_metadata row count does not match snapshot array")

    snapshot_metadata = snapshot_metadata.copy()
    snapshot_metadata.insert(0, "feature_row_id", np.arange(len(snapshot_metadata)))
    state_cols = [
        "feature_row_id",
        "run_id",
        "Tw",
        "state_recovery_time",
        "PC1",
        "PC2",
        "lag_time",
        "presister_like",
        "UMAP1",
        "UMAP2",
    ]
    state_info = cell_state[state_cols].copy()
    state_info["presister_like"] = state_info["presister_like"].astype(bool)

    print("[loop-bins] reconstructing cycle lengths for each run")
    run_bins = build_run_cycle_bins(params, simulation_metadata)

    rows = []
    total = len(snapshot_metadata)
    for i, meta in enumerate(snapshot_metadata.itertuples(index=False)):
        if i % 5000 == 0:
            print(f"[loop-bins] snapshots {i}/{total}")
        run_id = int(meta.run_id)
        run_info = run_bins[run_id]
        cycle_mags = compute_cycle_magnetization(
            np.asarray(snapshots[int(meta.feature_row_id)]),
            run_info["cycle_starts"],
            run_info["cycle_lengths"],
        )
        for bin_def in run_info["bins"]:
            mask = bin_def["mask"]
            values = cycle_mags[mask]
            rows.append(
                {
                    "feature_row_id": int(meta.feature_row_id),
                    "run_id": run_id,
                    "Tw": int(meta.Tw),
                    "state_recovery_time": int(meta.state_recovery_time),
                    "bin_type": bin_def["bin_type"],
                    "bin_id": bin_def["bin_id"],
                    "bin_label": bin_def["bin_label"],
                    "length_min": bin_def["length_min"],
                    "length_max": bin_def["length_max"],
                    "mean_cycle_activation": (
                        float(np.mean(values)) if len(values) else np.nan
                    ),
                    "n_cycles": int(len(values)),
                }
            )

    long_table = pd.DataFrame(rows)
    long_table = long_table.merge(
        state_info,
        on=["feature_row_id", "run_id", "Tw", "state_recovery_time"],
        how="left",
    )
    long_table.to_csv(output_dir / "loop_bin_activity_long.csv", index=False)

    pc1_window = compute_loop_bin_pc1_windows(
        long_table,
        state_recovery_time=args.state_recovery_time,
        window_size=args.window_size,
        bin_type="quantile",
    )
    by_Tw = summarize_loop_bins_by_group(
        long_table[long_table["state_recovery_time"] == args.state_recovery_time],
        ["Tw", "bin_type", "bin_id", "bin_label"],
    )
    by_recovery_time = summarize_loop_bins_by_group(
        long_table,
        ["state_recovery_time", "bin_type", "bin_id", "bin_label"],
    )
    correlations = compute_loop_bin_correlations(long_table)

    pc1_window.to_csv(output_dir / "loop_bin_activity_by_PC1_window.csv", index=False)
    by_Tw.to_csv(output_dir / "loop_bin_activity_by_Tw.csv", index=False)
    by_recovery_time.to_csv(
        output_dir / "loop_bin_activity_by_recovery_time.csv", index=False
    )
    correlations.to_csv(output_dir / "loop_bin_correlation_summary.csv", index=False)

    plot_loop_bin_pc1(
        pc1_window, output_dir / "loop_bin_activity_along_PC1.png"
    )
    plot_loop_bin_heatmap(
        by_Tw,
        row_col="Tw",
        output_path=output_dir / "loop_bin_activity_by_Tw_heatmap.png",
        title="Quantile loop-bin activity by Tw",
    )
    plot_loop_bin_heatmap(
        by_recovery_time,
        row_col="state_recovery_time",
        output_path=output_dir / "loop_bin_activity_by_recovery_time_heatmap.png",
        title="Quantile loop-bin activity by recovery time",
    )
    plot_loop_bin_lag_correlations(
        correlations, output_dir / "loop_bin_correlation_with_lag_time.png"
    )
    print(f"[loop-bins] saved {len(long_table)} long-form rows")


def summarize_loop_bins_by_group(table, group_cols):
    summary = (
        table.groupby(group_cols)["mean_cycle_activation"]
        .agg(["mean", "std", "count"])
        .reset_index()
        .rename(
            columns={
                "mean": "mean_cycle_activation",
                "std": "std_cycle_activation",
                "count": "n_snapshots",
            }
        )
    )
    summary["sem_cycle_activation"] = summary["std_cycle_activation"] / np.sqrt(
        summary["n_snapshots"]
    )
    return summary


def compute_loop_bin_pc1_windows(
    long_table, state_recovery_time=0, window_size=100, bin_type="quantile"
):
    table = long_table[
        (long_table["state_recovery_time"] == state_recovery_time)
        & (long_table["bin_type"] == bin_type)
    ].copy()
    states = (
        table[["feature_row_id", "PC1"]]
        .drop_duplicates()
        .sort_values("PC1")
        .reset_index(drop=True)
    )
    if states.empty:
        return pd.DataFrame()

    window_size = int(min(max(1, window_size), len(states)))
    starts = [0] if len(states) <= window_size else range(0, len(states) - window_size + 1)
    rows = []
    for start in starts:
        window_ids = states.iloc[start : start + window_size]
        window = table[table["feature_row_id"].isin(window_ids["feature_row_id"])]
        center = float(window_ids["PC1"].mean())
        grouped = summarize_loop_bins_by_group(
            window, ["bin_type", "bin_id", "bin_label"]
        )
        grouped.insert(0, "PC1_window_center", center)
        grouped["n_cells_in_window"] = int(len(window_ids))
        grouped["window_size"] = window_size
        rows.append(grouped)
    return pd.concat(rows, ignore_index=True)


def compute_loop_bin_correlations(long_table):
    rows = []
    for keys, group in long_table.groupby(["bin_type", "bin_id", "bin_label"]):
        bin_type, bin_id, bin_label = keys
        for target in ["PC1", "lag_time"]:
            valid = group[["mean_cycle_activation", target]].dropna()
            if len(valid) < 3 or valid["mean_cycle_activation"].std() == 0:
                corr = np.nan
            else:
                corr = float(
                    np.corrcoef(valid["mean_cycle_activation"], valid[target])[0, 1]
                )
            rows.append(
                {
                    "bin_type": bin_type,
                    "bin_id": int(bin_id),
                    "bin_label": bin_label,
                    "target": target,
                    "pearson_correlation": corr,
                    "n_snapshots": int(len(valid)),
                }
            )
    return pd.DataFrame(rows)


def plot_loop_bin_pc1(pc1_table, output_path):
    table = pc1_table[pc1_table["bin_type"] == "quantile"].copy()
    fig, ax = plt.subplots(figsize=(6.0, 4.2))
    for label, group in table.groupby("bin_label"):
        group = group.sort_values("PC1_window_center")
        ax.plot(
            group["PC1_window_center"],
            group["mean_cycle_activation"],
            label=label,
        )
    ax.set_xlabel("PC1 window center")
    ax.set_ylabel("Mean cycle activation")
    ax.set_title("Quantile loop-bin activity along PC1")
    ax.legend(frameon=False, ncol=3)
    fig.tight_layout()
    fig.savefig(output_path, dpi=300)
    plt.close(fig)


def plot_loop_bin_heatmap(summary, row_col, output_path, title):
    table = summary[summary["bin_type"] == "quantile"].copy()
    pivot = table.pivot(
        index=row_col, columns="bin_label", values="mean_cycle_activation"
    ).sort_index()
    fig, ax = plt.subplots(figsize=(6.0, 4.2))
    image = ax.imshow(pivot.to_numpy(dtype=float), aspect="auto", cmap="coolwarm")
    ax.set_xticks(np.arange(len(pivot.columns)))
    ax.set_xticklabels(pivot.columns)
    ax.set_yticks(np.arange(len(pivot.index)))
    ax.set_yticklabels(pivot.index)
    ax.set_xlabel("Loop-length quantile bin")
    ax.set_ylabel(row_col)
    ax.set_title(title)
    fig.colorbar(image, ax=ax, label="Mean cycle activation")
    fig.tight_layout()
    fig.savefig(output_path, dpi=300)
    plt.close(fig)


def plot_loop_bin_lag_correlations(correlations, output_path):
    table = correlations[
        (correlations["bin_type"] == "quantile")
        & (correlations["target"] == "lag_time")
    ].copy()
    table = table.sort_values("bin_id")
    fig, ax = plt.subplots(figsize=(5.2, 3.8))
    ax.bar(table["bin_label"], table["pearson_correlation"], color="#2a9d8f")
    ax.axhline(0, color="#333333", linewidth=0.8)
    ax.set_xlabel("Loop-length quantile bin")
    ax.set_ylabel("Correlation with lag time")
    ax.set_title("Loop-bin activity vs lag time")
    fig.tight_layout()
    fig.savefig(output_path, dpi=300)
    plt.close(fig)


def main():
    args = parse_args()
    ensure_dir(args.output_dir)
    with open(args.simulation_dir / "params.json", "r", encoding="utf-8") as handle:
        params = json.load(handle)

    run_tail = args.tail_cluster or not args.loop_bins
    run_loop = args.loop_bins or not args.tail_cluster

    if run_tail:
        run_tail_cluster_matching(args, params)
    if run_loop:
        compute_loop_bin_activity(args, params)

    print(f"[done] outputs written to {args.output_dir}")


if __name__ == "__main__":
    main()

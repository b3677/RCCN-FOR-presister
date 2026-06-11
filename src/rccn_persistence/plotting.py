import matplotlib.pyplot as plt
import numpy as np

from .observables import classify_cell_fate


def _plot_density_hist(ax, values, bins, color, orientation="vertical"):
    values = np.asarray(values, dtype=float)
    values = values[np.isfinite(values)]
    if len(values) == 0:
        return
    ax.hist(
        values,
        bins=bins,
        density=True,
        histtype="stepfilled",
        alpha=0.28,
        color=color,
        edgecolor=color,
        linewidth=1.0,
        orientation=orientation,
    )


def _clean_marginal_axis(ax):
    ax.tick_params(left=False, bottom=False, labelleft=False, labelbottom=False)
    for spine in ax.spines.values():
        spine.set_visible(False)


def plot_survival_by_Tw(survival_table, output_path):
    fig, ax = plt.subplots(figsize=(6, 4))
    for Tw, group in survival_table.groupby("Tw"):
        ax.plot(group["time"], group["survival"], label=f"Tw={Tw}")
    ax.set_xlabel("recovery time")
    ax.set_ylabel("survival")
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(output_path, dpi=300)
    plt.close(fig)


def plot_pca_by_column(pca_scores, metadata, column, output_path):
    merged = pca_scores.merge(metadata, on="run_id")
    fig, ax = plt.subplots(figsize=(5, 4))
    scatter = ax.scatter(merged["PC1"], merged["PC2"], c=merged[column], s=35)
    ax.set_xlabel("PC1")
    ax.set_ylabel("PC2")
    fig.colorbar(scatter, ax=ax, label=column)
    fig.tight_layout()
    fig.savefig(output_path, dpi=300)
    plt.close(fig)


def plot_pca_by_cluster(pca_scores, cluster_labels, output_path):
    merged = pca_scores.merge(cluster_labels, on="run_id")
    fig, ax = plt.subplots(figsize=(5, 4))
    scatter = ax.scatter(merged["PC1"], merged["PC2"], c=merged["cluster"], s=35)
    ax.set_xlabel("PC1")
    ax.set_ylabel("PC2")
    fig.colorbar(scatter, ax=ax, label="cluster")
    fig.tight_layout()
    fig.savefig(output_path, dpi=300)
    plt.close(fig)


def plot_cluster_occupancy(occupancy_table, output_path):
    pivot = occupancy_table.pivot(index="Tw", columns="cluster", values="fraction")
    fig, ax = plt.subplots(figsize=(6, 4))
    pivot.plot(kind="bar", stacked=True, ax=ax)
    ax.set_ylabel("fraction")
    fig.tight_layout()
    fig.savefig(output_path, dpi=300)
    plt.close(fig)


def plot_pca_by_fate(
    pca_scores, metadata, output_path, persister_recovery_time=None
):
    metadata_with_fate = classify_cell_fate(metadata, persister_recovery_time)
    merged = pca_scores.merge(metadata_with_fate[["run_id", "fate"]], on="run_id")
    colors = {"regrowth": "#4C78A8", "persister": "#E45756"}

    fig, ax = plt.subplots(figsize=(5, 4))
    for fate in ["regrowth", "persister"]:
        group = merged[merged["fate"] == fate]
        if group.empty:
            continue
        ax.scatter(
            group["PC1"],
            group["PC2"],
            s=35,
            label=fate,
            color=colors[fate],
            alpha=0.85,
            edgecolors="none",
        )
    ax.set_xlabel("PC1")
    ax.set_ylabel("PC2")
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(output_path, dpi=300)
    plt.close(fig)


def plot_fate_fraction_by_Tw(fate_occupancy, output_path):
    pivot = fate_occupancy.pivot(index="Tw", columns="fate", values="fraction")
    pivot = pivot.reindex(columns=["regrowth", "persister"]).fillna(0.0)

    fig, ax = plt.subplots(figsize=(6, 4))
    pivot.plot(
        kind="bar",
        stacked=True,
        ax=ax,
        color=["#4C78A8", "#E45756"],
    )
    ax.set_xlabel("Tw")
    ax.set_ylabel("fraction")
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(output_path, dpi=300)
    plt.close(fig)


def plot_figA_recovery_dynamics(recovery_dynamics, output_path):
    fig, ax = plt.subplots(figsize=(6.5, 4.2))
    for Tw, group in recovery_dynamics.groupby("Tw"):
        group = group.sort_values("recovery_time")
        ax.plot(
            group["recovery_time"],
            group["mean_recovery_observable"],
            label=f"Tw={Tw} min",
            linewidth=1.8,
        )
        sem = group["sem_recovery_observable"].fillna(0.0)
        ax.fill_between(
            group["recovery_time"],
            group["mean_recovery_observable"] - sem,
            group["mean_recovery_observable"] + sem,
            alpha=0.15,
        )
    ax.set_xlabel("Recovery time after nutrient restoration (min)")
    ax.set_ylabel("Mean cycle-averaged magnetization")
    ax.set_title("RCCN ageing reproduction")
    ax.legend(frameon=False, fontsize=8)
    fig.tight_layout()
    fig.savefig(output_path, dpi=300)
    plt.close(fig)


def plot_figA_recovery_survival_semilog_loglog(recovery_survival, output_path):
    fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.2))
    for Tw, group in recovery_survival.groupby("Tw"):
        group = group.sort_values("recovery_time")
        label = f"Tw={Tw} min"
        semilog = group[group["survival"] > 0]
        axes[0].plot(
            semilog["recovery_time"],
            semilog["survival"],
            label=label,
            linewidth=1.8,
        )

        loglog = group[(group["recovery_time"] > 0) & (group["survival"] > 0)]
        axes[1].plot(
            loglog["recovery_time"],
            loglog["survival"],
            label=label,
            linewidth=1.8,
        )

    axes[0].set_yscale("log")
    axes[0].set_xlabel("Recovery time after nutrient restoration (min)")
    axes[0].set_ylabel("1 - CDF (fraction unrecovered)")
    axes[0].set_title("Semi-log")
    axes[0].legend(frameon=False, fontsize=8)

    axes[1].set_xscale("log")
    axes[1].set_yscale("log")
    axes[1].set_xlabel("Recovery time after nutrient restoration (min)")
    axes[1].set_ylabel("1 - CDF")
    axes[1].set_title("Log-log")

    fig.suptitle("RCCN recovery survival using M <= 0 recovery definition")
    fig.tight_layout()
    fig.savefig(output_path, dpi=300)
    plt.close(fig)


def plot_figB_umap_by_Tw_recovery_time(
    cell_state_table,
    tail_fraction_table,
    output_path,
    selected_recovery_times=None,
    recovery_time_colors=None,
):
    selected_Tw = [0, 488, 1346]
    if selected_recovery_times is None:
        selected_recovery_times = [0, 500, 2000]
    selected_recovery_times = [int(time) for time in selected_recovery_times]
    missing = set(selected_recovery_times) - set(cell_state_table["state_recovery_time"])
    if missing:
        raise ValueError(f"Fig. B is missing recovery-time snapshots: {sorted(missing)}")

    fig = plt.figure(figsize=(13.5, 4.8))
    outer = fig.add_gridspec(1, 3, wspace=0.25)
    colors = (
        recovery_time_colors
        if recovery_time_colors is not None
        else {0: "#FFB703", 500: "#5A189A", 2000: "#E63914"}
    )
    xlim = (cell_state_table["UMAP1"].min(), cell_state_table["UMAP1"].max())
    ylim = (cell_state_table["UMAP2"].min(), cell_state_table["UMAP2"].max())
    xbins = np.linspace(xlim[0], xlim[1], 30)
    ybins = np.linspace(ylim[0], ylim[1], 30)

    handles = []
    labels = []
    for panel_idx, Tw in enumerate(selected_Tw):
        grid = outer[panel_idx].subgridspec(
            2, 2, height_ratios=[1, 4], width_ratios=[4, 1], hspace=0.03, wspace=0.03
        )
        ax_top = fig.add_subplot(grid[0, 0])
        ax = fig.add_subplot(grid[1, 0])
        ax_right = fig.add_subplot(grid[1, 1])
        group = cell_state_table[cell_state_table["Tw"] == Tw]
        for recovery_time in selected_recovery_times:
            subset = group[group["state_recovery_time"] == recovery_time]
            scatter = ax.scatter(
                subset["UMAP1"],
                subset["UMAP2"],
                s=12,
                alpha=0.75,
                color=colors.get(recovery_time, "#777777"),
                edgecolors="none",
                label=f"{recovery_time} min",
            )
            _plot_density_hist(
                ax_top, subset["UMAP1"], xbins, colors.get(recovery_time, "#777777")
            )
            _plot_density_hist(
                ax_right,
                subset["UMAP2"],
                ybins,
                colors.get(recovery_time, "#777777"),
                orientation="horizontal",
            )
            if recovery_time not in labels:
                handles.append(scatter)
                labels.append(recovery_time)
        centroids = (
            group.groupby("state_recovery_time")[["UMAP1", "UMAP2"]]
            .mean()
            .reindex(selected_recovery_times)
            .dropna()
        )
        for start, end in zip(centroids.index[:-1], centroids.index[1:]):
            start_xy = centroids.loc[start, ["UMAP1", "UMAP2"]].to_numpy()
            end_xy = centroids.loc[end, ["UMAP1", "UMAP2"]].to_numpy()
            ax.annotate(
                "",
                xy=end_xy,
                xytext=start_xy,
                arrowprops={"arrowstyle": "->", "color": "#222222", "lw": 1.4},
            )
        ax.scatter(
            centroids["UMAP1"],
            centroids["UMAP2"],
            s=38,
            color="#222222",
            marker="x",
            linewidths=1.2,
            zorder=5,
        )
        for recovery_time, row in centroids.iterrows():
            ax.text(
                row["UMAP1"],
                row["UMAP2"],
                f" {int(recovery_time)}",
                color="#222222",
                fontsize=6,
                ha="left",
                va="center",
                zorder=6,
            )
        tail = tail_fraction_table[tail_fraction_table["Tw"] == Tw]
        tail_text = ""
        if not tail.empty:
            row = tail.iloc[0]
            tail_text = (
                f"Tail fraction = {row['TailFraction']:.3f} "
                f"+/- {row['TailFractionSTD']:.3f}"
            )
        ax_top.set_title(f"Tw = {Tw} min", fontsize=10, pad=2)
        ax.set_xlabel("UMAP1")
        ax.text(
            0.03,
            0.03,
            tail_text,
            transform=ax.transAxes,
            ha="left",
            va="bottom",
            fontsize=7,
            bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.75},
        )
        ax.set_xlim(xlim)
        ax.set_ylim(ylim)
        ax_top.set_xlim(xlim)
        ax_right.set_ylim(ylim)
        _clean_marginal_axis(ax_top)
        _clean_marginal_axis(ax_right)
        if panel_idx == 0:
            ax.set_ylabel("UMAP2")
        else:
            ax.set_yticklabels([])
    fig.legend(
        handles,
        [f"{label} min" for label in labels],
        frameon=False,
        loc="upper center",
        ncol=min(len(labels), 6),
    )
    fig.subplots_adjust(left=0.06, right=0.98, bottom=0.14, top=0.84)
    fig.savefig(output_path, dpi=300)
    plt.close(fig)


def plot_figB_umap_recovery_time_exploration(
    cell_state_table, tail_fraction_table, output_path
):
    selected_recovery_times = [0, 250, 500, 1000, 2000, 4000]
    colors = {
        0: "#FFB703",
        250: "#2A9D8F",
        500: "#5A189A",
        1000: "#457B9D",
        2000: "#E63914",
        4000: "#6D597A",
    }
    plot_figB_umap_by_Tw_recovery_time(
        cell_state_table,
        tail_fraction_table,
        output_path,
        selected_recovery_times=selected_recovery_times,
        recovery_time_colors=colors,
    )


def plot_figC_cluster_occupancy_and_lag(
    cluster_summary, cell_state_table, output_path, state_recovery_time_for_summary=0
):
    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    pivot = cluster_summary.pivot(
        index="Tw", columns="cluster_id", values="cluster_fraction"
    ).fillna(0.0)
    cluster_colors = {0: "#4198AC", 1: "#7BC0CD", 2: "#DBCB92"}
    bar_colors = [cluster_colors.get(cluster, "#999999") for cluster in pivot.columns]
    pivot.plot(kind="bar", stacked=True, ax=axes[0], color=bar_colors)
    axes[0].set_xlabel("Waiting time Tw (min)")
    axes[0].set_ylabel("Fraction of simulations")
    axes[0].legend(
        title="Spin-state cluster",
        frameon=False,
        fontsize=8,
        bbox_to_anchor=(1.02, 1.0),
        loc="upper left",
    )

    table = cell_state_table[
        cell_state_table["state_recovery_time"] == state_recovery_time_for_summary
    ]
    clusters = sorted(table["cluster_id"].dropna().unique())
    values = [
        table.loc[table["cluster_id"] == cluster, "lag_time"].dropna().to_numpy()
        for cluster in clusters
    ]
    if any(len(v) for v in values):
        axes[1].violinplot(values, positions=np.arange(len(clusters)), showmedians=True)
        jitter_rng = np.random.default_rng(1)
        for pos, vals in enumerate(values):
            if len(vals) == 0:
                continue
            x = pos + jitter_rng.normal(0, 0.035, size=len(vals))
            axes[1].scatter(
                x,
                vals,
                s=8,
                alpha=0.35,
                color=cluster_colors.get(clusters[pos], "#333333"),
                edgecolors="none",
            )
    axes[1].set_xticks(np.arange(len(clusters)))
    axes[1].set_xticklabels([str(cluster) for cluster in clusters])
    axes[1].set_xlabel("Spin-state cluster")
    axes[1].set_ylabel("Recovery / lag time (min)")
    fig.tight_layout()
    fig.savefig(output_path, dpi=300)
    plt.close(fig)


def plot_figE_presister_like_pca_umap(
    cell_state_table, output_path, state_recovery_time_for_figE=0
):
    table = cell_state_table[
        cell_state_table["state_recovery_time"] == state_recovery_time_for_figE
    ]
    colors = {"normal": "#163273", "presister-like": "#FA517C"}
    fig = plt.figure(figsize=(12.5, 4.8))
    outer = fig.add_gridspec(1, 2, wspace=0.26)
    pca_grid = outer[0].subgridspec(
        2, 2, height_ratios=[1, 4], width_ratios=[4, 1], hspace=0.03, wspace=0.03
    )
    ax_top = fig.add_subplot(pca_grid[0, 0])
    ax_pca = fig.add_subplot(pca_grid[1, 0])
    ax_right = fig.add_subplot(pca_grid[1, 1])
    umap_grid = outer[1].subgridspec(
        2, 2, height_ratios=[1, 4], width_ratios=[4, 1], hspace=0.03, wspace=0.03
    )
    ax_umap_top = fig.add_subplot(umap_grid[0, 0])
    ax_umap = fig.add_subplot(umap_grid[1, 0])
    ax_umap_right = fig.add_subplot(umap_grid[1, 1])
    pc1_bins = np.linspace(table["PC1"].min(), table["PC1"].max(), 35)
    pc2_bins = np.linspace(table["PC2"].min(), table["PC2"].max(), 35)
    umap1_bins = np.linspace(table["UMAP1"].min(), table["UMAP1"].max(), 35)
    umap2_bins = np.linspace(table["UMAP2"].min(), table["UMAP2"].max(), 35)
    for state in ["normal", "presister-like"]:
        group = table[table["state_label"] == state]
        ax_pca.scatter(
            group["PC1"],
            group["PC2"],
            s=14,
            alpha=0.75,
            color=colors[state],
            edgecolors="none",
            label=state,
        )
        _plot_density_hist(ax_top, group["PC1"], pc1_bins, colors[state])
        _plot_density_hist(
            ax_right, group["PC2"], pc2_bins, colors[state], orientation="horizontal"
        )
        ax_umap.scatter(
            group["UMAP1"],
            group["UMAP2"],
            s=14,
            alpha=0.75,
            color=colors[state],
            edgecolors="none",
            label=state,
        )
        _plot_density_hist(ax_umap_top, group["UMAP1"], umap1_bins, colors[state])
        _plot_density_hist(
            ax_umap_right,
            group["UMAP2"],
            umap2_bins,
            colors[state],
            orientation="horizontal",
        )
    ax_pca.set_xlabel("PC1")
    ax_pca.set_ylabel("PC2")
    ax_pca.set_title("PCA")
    ax_top.set_xlim(ax_pca.get_xlim())
    ax_right.set_ylim(ax_pca.get_ylim())
    _clean_marginal_axis(ax_top)
    _clean_marginal_axis(ax_right)
    ax_umap.set_xlabel("UMAP1")
    ax_umap.set_ylabel("UMAP2")
    ax_umap.set_title("UMAP")
    ax_umap_top.set_xlim(ax_umap.get_xlim())
    ax_umap_right.set_ylim(ax_umap.get_ylim())
    _clean_marginal_axis(ax_umap_top)
    _clean_marginal_axis(ax_umap_right)
    ax_umap.legend(frameon=False)
    fig.suptitle("Tail-fraction-defined presister-like cells")
    fig.subplots_adjust(left=0.07, right=0.98, bottom=0.14, top=0.86)
    fig.savefig(output_path, dpi=300)
    plt.close(fig)


def plot_figD_cycle_groups_along_PC1(
    cycle_pc1_moving_average,
    cell_state_table,
    output_path,
    state_recovery_time_for_figD=0,
    title_suffix="",
):
    states = cell_state_table[
        cell_state_table["state_recovery_time"] == state_recovery_time_for_figD
    ]
    fig, axes = plt.subplots(2, 1, figsize=(6.5, 6), sharex=True)
    axes[0].hist(states["PC1"].dropna(), bins=30, color="#777777", alpha=0.8)
    axes[0].set_ylabel("Cell count")
    title = "RCCN cycle activity along PC1 state axis"
    if title_suffix:
        title = f"{title} ({title_suffix})"
    axes[0].set_title(title)

    colors = {"short": "#FFB703", "medium": "#5A189A", "long": "#E63914"}
    for cycle_group, group in cycle_pc1_moving_average.groupby("cycle_group"):
        group = group.sort_values("PC1_window_center")
        axes[1].plot(
            group["PC1_window_center"],
            group["mean_cycle_activation"],
            label=f"{cycle_group} cycles",
            color=colors.get(cycle_group),
        )
        sem = group["sem_cycle_activation"].fillna(0.0)
        axes[1].fill_between(
            group["PC1_window_center"],
            group["mean_cycle_activation"] - sem,
            group["mean_cycle_activation"] + sem,
            color=colors.get(cycle_group),
            alpha=0.15,
        )
    axes[1].set_xlabel("PC1 score")
    axes[1].set_ylabel("Mean cycle magnetization")
    axes[1].legend(frameon=False)
    fig.tight_layout()
    fig.savefig(output_path, dpi=300)
    plt.close(fig)

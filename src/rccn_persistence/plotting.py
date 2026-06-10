import matplotlib.pyplot as plt
import numpy as np

from .observables import classify_cell_fate


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


def plot_figB_umap_by_Tw_recovery_time(
    cell_state_table, tail_fraction_table, output_path
):
    selected_Tw = [0, 488, 1346]
    selected_recovery_times = [0, 20, 120]
    missing = set(selected_recovery_times) - set(cell_state_table["state_recovery_time"])
    if missing:
        raise ValueError(f"Fig. B is missing recovery-time snapshots: {sorted(missing)}")

    fig, axes = plt.subplots(1, 3, figsize=(11, 3.8), sharex=True, sharey=True)
    colors = {0: "#4C78A8", 20: "#59A14F", 120: "#E15759"}
    xlim = (cell_state_table["UMAP1"].min(), cell_state_table["UMAP1"].max())
    ylim = (cell_state_table["UMAP2"].min(), cell_state_table["UMAP2"].max())

    handles = []
    labels = []
    for ax, Tw in zip(axes, selected_Tw):
        group = cell_state_table[cell_state_table["Tw"] == Tw]
        for recovery_time in selected_recovery_times:
            subset = group[group["state_recovery_time"] == recovery_time]
            scatter = ax.scatter(
                subset["UMAP1"],
                subset["UMAP2"],
                s=12,
                alpha=0.75,
                color=colors[recovery_time],
                edgecolors="none",
                label=f"{recovery_time} min",
            )
            if recovery_time not in labels:
                handles.append(scatter)
                labels.append(recovery_time)
        tail = tail_fraction_table[tail_fraction_table["Tw"] == Tw]
        tail_text = ""
        if not tail.empty:
            row = tail.iloc[0]
            tail_text = (
                f"Tail fraction = {row['TailFraction']:.3f} "
                f"+/- {row['TailFractionSTD']:.3f}"
            )
        ax.set_title(f"Tw = {Tw} min")
        ax.set_xlabel("UMAP1")
        ax.text(0.5, -0.22, tail_text, transform=ax.transAxes, ha="center", fontsize=8)
        ax.set_xlim(xlim)
        ax.set_ylim(ylim)
    axes[0].set_ylabel("UMAP2")
    fig.legend(handles, [f"{label} min" for label in labels], frameon=False, loc="upper center", ncol=3)
    fig.tight_layout(rect=[0, 0, 1, 0.9])
    fig.savefig(output_path, dpi=300)
    plt.close(fig)


def plot_figC_cluster_occupancy_and_lag(
    cluster_summary, cell_state_table, output_path, state_recovery_time_for_summary=0
):
    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    pivot = cluster_summary.pivot(
        index="Tw", columns="cluster_id", values="cluster_fraction"
    ).fillna(0.0)
    pivot.plot(kind="bar", stacked=True, ax=axes[0])
    axes[0].set_xlabel("Waiting time Tw (min)")
    axes[0].set_ylabel("Fraction of simulations")
    axes[0].legend(title="Spin-state cluster", frameon=False, fontsize=8)

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
            axes[1].scatter(x, vals, s=8, alpha=0.35, color="#333333", edgecolors="none")
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
    colors = {"normal": "#4C78A8", "presister-like": "#E15759"}
    fig, axes = plt.subplots(1, 2, figsize=(9, 4))
    for state in ["normal", "presister-like"]:
        group = table[table["state_label"] == state]
        axes[0].scatter(
            group["PC1"],
            group["PC2"],
            s=14,
            alpha=0.75,
            color=colors[state],
            edgecolors="none",
            label=state,
        )
        axes[1].scatter(
            group["UMAP1"],
            group["UMAP2"],
            s=14,
            alpha=0.75,
            color=colors[state],
            edgecolors="none",
            label=state,
        )
    axes[0].set_xlabel("PC1")
    axes[0].set_ylabel("PC2")
    axes[0].set_title("PCA")
    axes[1].set_xlabel("UMAP1")
    axes[1].set_ylabel("UMAP2")
    axes[1].set_title("UMAP")
    axes[1].legend(frameon=False)
    fig.suptitle("Tail-fraction-defined presister-like cells")
    fig.tight_layout()
    fig.savefig(output_path, dpi=300)
    plt.close(fig)


def plot_figD_cycle_groups_along_PC1(
    cycle_pc1_moving_average, cell_state_table, output_path, state_recovery_time_for_figD=0
):
    states = cell_state_table[
        cell_state_table["state_recovery_time"] == state_recovery_time_for_figD
    ]
    fig, axes = plt.subplots(2, 1, figsize=(6.5, 6), sharex=True)
    axes[0].hist(states["PC1"].dropna(), bins=30, color="#777777", alpha=0.8)
    axes[0].set_ylabel("Cell count")
    axes[0].set_title("RCCN cycle activity along PC1 state axis")

    colors = {"short": "#4C78A8", "medium": "#F28E2B", "long": "#E15759"}
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

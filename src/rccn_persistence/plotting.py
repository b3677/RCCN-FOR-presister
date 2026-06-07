import matplotlib.pyplot as plt


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


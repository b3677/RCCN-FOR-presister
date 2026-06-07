import numpy as np
import pandas as pd


def center_spin_matrix(X_spin):
    return X_spin - X_spin.mean(axis=0, keepdims=True)


def run_pca_on_spins(X_spin, n_components):
    X_centered = center_spin_matrix(np.asarray(X_spin, dtype=float))
    max_components = min(n_components, X_centered.shape[0], X_centered.shape[1])
    U, singular_values, _ = np.linalg.svd(X_centered, full_matrices=False)
    scores = U[:, :max_components] * singular_values[:max_components]

    variance = singular_values**2 / max(X_centered.shape[0] - 1, 1)
    total_variance = variance.sum()
    if total_variance == 0:
        explained = np.zeros(max_components)
    else:
        explained = variance[:max_components] / total_variance

    return scores, explained


def cluster_pca_scores(pca_scores, n_clusters, rng=None, max_iter=100):
    rng = np.random.default_rng(1) if rng is None else rng
    pca_scores = np.asarray(pca_scores, dtype=float)
    if pca_scores.shape[0] < n_clusters:
        raise ValueError("n_clusters cannot be larger than the number of samples")

    initial_idx = rng.choice(pca_scores.shape[0], size=n_clusters, replace=False)
    centers = pca_scores[initial_idx].copy()

    for _ in range(max_iter):
        distances = ((pca_scores[:, None, :] - centers[None, :, :]) ** 2).sum(axis=2)
        labels = np.argmin(distances, axis=1)
        new_centers = centers.copy()
        for cluster in range(n_clusters):
            mask = labels == cluster
            if np.any(mask):
                new_centers[cluster] = pca_scores[mask].mean(axis=0)
        if np.allclose(new_centers, centers):
            break
        centers = new_centers

    return labels


def summarize_cluster_occupancy(metadata, cluster_labels):
    metadata_with_cluster = metadata.copy()
    metadata_with_cluster["cluster"] = cluster_labels
    counts = (
        metadata_with_cluster.groupby(["Tw", "cluster"])
        .size()
        .rename("count")
        .reset_index()
    )
    counts["fraction"] = counts["count"] / counts.groupby("Tw")["count"].transform("sum")
    return counts


def summarize_recovery_by_cluster(metadata, cluster_labels):
    metadata_with_cluster = metadata.copy()
    metadata_with_cluster["cluster"] = cluster_labels
    return (
        metadata_with_cluster.groupby("cluster")["recovery_time"]
        .agg(["count", "mean", "median"])
        .reset_index()
    )


def run_spin_clustering_analysis(simulation_data, analysis_params):
    X_spin = simulation_data["spin_release"]
    metadata = simulation_data["metadata"]
    scores, explained = run_pca_on_spins(X_spin, analysis_params["pca_components"])
    rng = np.random.default_rng(analysis_params.get("random_seed", 1))
    labels = cluster_pca_scores(scores, analysis_params["n_clusters"], rng=rng)

    pca_scores = pd.DataFrame(
        scores, columns=[f"PC{i + 1}" for i in range(scores.shape[1])]
    )
    pca_scores["run_id"] = metadata["run_id"].to_numpy()

    cluster_labels = pd.DataFrame(
        {
            "run_id": metadata["run_id"].to_numpy(),
            "cluster": labels,
        }
    )

    return {
        "pca_scores": pca_scores,
        "explained_variance": pd.DataFrame(
            {
                "PC": np.arange(1, len(explained) + 1),
                "explained_variance_ratio": explained,
            }
        ),
        "cluster_labels": cluster_labels,
        "cluster_occupancy_by_Tw": summarize_cluster_occupancy(metadata, labels),
        "recovery_time_by_cluster": summarize_recovery_by_cluster(metadata, labels),
    }

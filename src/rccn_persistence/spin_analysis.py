import numpy as np
import pandas as pd

from .observables import (
    assign_presister_like_by_tail_fraction,
    compute_recovery_dynamics_by_Tw,
    load_tail_fraction_table,
    summarize_cluster_by_Tw,
)


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


def build_spin_feature_matrix(simulation_data, feature_mode="selected_snapshots"):
    if feature_mode == "selected_snapshots":
        X_features = simulation_data["selected_spin_snapshots"]
        feature_metadata = simulation_data["snapshot_metadata"].copy()
    elif feature_mode == "release":
        X_features = simulation_data["spin_release"]
        feature_metadata = simulation_data["metadata"].copy()
        feature_metadata["state_recovery_time"] = 0
        feature_metadata["absolute_snapshot_time"] = feature_metadata["snapshot_time"]
    elif feature_mode == "early":
        X_features = simulation_data["spin_early_recovery"]
        feature_metadata = simulation_data["metadata"].copy()
        feature_metadata["state_recovery_time"] = feature_metadata[
            "early_recovery_snapshot_time"
        ] - feature_metadata["snapshot_time"]
        feature_metadata["absolute_snapshot_time"] = feature_metadata[
            "early_recovery_snapshot_time"
        ]
    elif feature_mode == "release_plus_early":
        X_features = np.hstack(
            [simulation_data["spin_release"], simulation_data["spin_early_recovery"]]
        )
        feature_metadata = simulation_data["metadata"].copy()
        feature_metadata["state_recovery_time"] = 0
        feature_metadata["absolute_snapshot_time"] = feature_metadata["snapshot_time"]
    else:
        raise ValueError(f"unknown feature_mode: {feature_mode}")

    X_features = np.asarray(X_features)
    if X_features.shape[0] != len(feature_metadata):
        raise ValueError("feature matrix row count does not match feature metadata")
    feature_metadata = feature_metadata.reset_index(drop=True)
    feature_metadata.insert(0, "feature_row_id", np.arange(len(feature_metadata)))
    return X_features, feature_metadata


def run_pca(X_features, n_components, method="full"):
    from sklearn.decomposition import IncrementalPCA, PCA

    max_components = min(n_components, X_features.shape[0], X_features.shape[1])

    if method == "incremental":
        batch_size = max(1024, max_components * 10)
        pca = IncrementalPCA(n_components=max_components, batch_size=batch_size)

        for start in range(0, X_features.shape[0], batch_size):
            stop = min(start + batch_size, X_features.shape[0])
            print(
                f"[analysis] PCA partial_fit rows {start}:{stop}",
                flush=True,
            )
            pca.partial_fit(np.asarray(X_features[start:stop], dtype=np.float32))

        score_chunks = []
        for start in range(0, X_features.shape[0], batch_size):
            stop = min(start + batch_size, X_features.shape[0])
            print(
                f"[analysis] PCA transform rows {start}:{stop}",
                flush=True,
            )
            score_chunks.append(
                pca.transform(np.asarray(X_features[start:stop], dtype=np.float32))
            )
        scores = np.vstack(score_chunks)
    elif method == "full":
        print("[analysis] converting feature matrix to float32 for full PCA", flush=True)
        pca = PCA(n_components=max_components, svd_solver="auto")
        scores = pca.fit_transform(np.asarray(X_features, dtype=np.float32))
    else:
        raise ValueError(f"unknown PCA method: {method}")

    pca_scores = pd.DataFrame(
        scores, columns=[f"PC{i + 1}" for i in range(scores.shape[1])]
    )
    pca_scores.insert(0, "feature_row_id", np.arange(len(pca_scores)))
    explained = pd.DataFrame(
        {
            "PC": np.arange(1, len(pca.explained_variance_ratio_) + 1),
            "explained_variance_ratio": pca.explained_variance_ratio_,
        }
    )
    return pca_scores, explained


def run_umap(X_for_embedding, random_seed, n_neighbors=20, min_dist=0.2):
    try:
        from umap import UMAP
    except ImportError as exc:
        raise ImportError(
            "UMAP figures require the 'umap-learn' package. "
            "Install it before running final state analysis."
        ) from exc

    n_samples = X_for_embedding.shape[0]
    if n_samples < 3:
        raise ValueError("UMAP requires at least 3 sampled states")
    n_neighbors = max(2, min(int(n_neighbors), n_samples - 1))
    reducer = UMAP(
        n_components=2,
        n_neighbors=n_neighbors,
        min_dist=min_dist,
        random_state=random_seed,
    )
    coords = reducer.fit_transform(X_for_embedding)
    umap_scores = pd.DataFrame(coords, columns=["UMAP1", "UMAP2"])
    umap_scores.insert(0, "feature_row_id", np.arange(len(umap_scores)))
    return umap_scores


def run_clustering(X_for_clustering, n_clusters, random_seed):
    from sklearn.cluster import KMeans

    if X_for_clustering.shape[0] < n_clusters:
        raise ValueError("n_clusters cannot be larger than number of sampled states")
    model = KMeans(n_clusters=n_clusters, random_state=random_seed, n_init=20)
    labels = model.fit_predict(X_for_clustering)
    return pd.DataFrame(
        {"feature_row_id": np.arange(len(labels)), "cluster_id": labels.astype(int)}
    )


def build_cell_state_table(
    feature_metadata, pca_scores, umap_scores, cluster_labels, labeled_metadata
):
    table = feature_metadata.merge(pca_scores, on="feature_row_id")
    table = table.merge(umap_scores, on="feature_row_id")
    table = table.merge(cluster_labels, on="feature_row_id")
    labels = labeled_metadata[
        [
            "run_id",
            "recovery_time",
            "recovered",
            "presister_like",
            "state_label",
        ]
    ]
    table = table.merge(labels, on="run_id", how="left")
    table["simulation_id"] = table["run_id"]
    table["lag_time"] = table["recovery_time"]
    table["recovered_label"] = table["recovered"].astype(bool)
    columns = [
        "simulation_id",
        "run_id",
        "feature_row_id",
        "Tw",
        "state_recovery_time",
        "absolute_snapshot_time",
        "recovery_time",
        "lag_time",
        "recovered_label",
        "cluster_id",
        "presister_like",
        "state_label",
        "PC1",
        "PC2",
        "UMAP1",
        "UMAP2",
    ]
    extra_pc_columns = [
        col for col in table.columns if col.startswith("PC") and col not in columns
    ]
    return table[columns + extra_pc_columns].sort_values(
        ["Tw", "run_id", "state_recovery_time"]
    )


def summarize_recovery_time_by_cluster(
    cell_state_table, state_recovery_time_for_summary=0
):
    table = cell_state_table[
        cell_state_table["state_recovery_time"] == state_recovery_time_for_summary
    ]
    return (
        table.groupby("cluster_id")["lag_time"]
        .agg(["count", "mean", "median"])
        .reset_index()
    )


def compute_cycle_pc1_moving_average(
    cell_state_table, cycle_group_table, state_recovery_time_for_figD=0, window_size=100
):
    states = cell_state_table[
        cell_state_table["state_recovery_time"] == state_recovery_time_for_figD
    ][["run_id", "state_recovery_time", "PC1"]]
    cycles = cycle_group_table[
        cycle_group_table["state_recovery_time"] == state_recovery_time_for_figD
    ]
    merged = states.merge(cycles, on=["run_id", "state_recovery_time"])
    merged = merged.sort_values("PC1").reset_index(drop=True)
    if merged.empty:
        return pd.DataFrame(
            columns=[
                "PC1_window_center",
                "cycle_group",
                "mean_cycle_activation",
                "sem_cycle_activation",
                "n_cells_in_window",
                "window_size",
            ]
        )

    window_size = int(min(max(1, window_size), len(merged)))
    if len(merged) <= window_size:
        starts = [0]
    else:
        starts = range(0, len(merged) - window_size + 1)

    rows = []
    for start in starts:
        window = merged.iloc[start : start + window_size]
        center = float(window["PC1"].mean())
        for group in ["short", "medium", "long"]:
            values = window[f"{group}_cycle_activation"].dropna()
            sem = values.std(ddof=1) / np.sqrt(len(values)) if len(values) > 1 else 0.0
            rows.append(
                {
                    "PC1_window_center": center,
                    "cycle_group": group,
                    "mean_cycle_activation": float(values.mean()),
                    "sem_cycle_activation": float(sem),
                    "n_cells_in_window": int(len(values)),
                    "window_size": window_size,
                }
            )
    return pd.DataFrame(rows)


def compute_cycle_pc1_moving_average_by_Tw(
    cell_state_table, cycle_group_table, state_recovery_time_for_figD=0, window_size=100
):
    tables = []
    for Tw in sorted(cell_state_table["Tw"].dropna().unique()):
        state_subset = cell_state_table[cell_state_table["Tw"] == Tw]
        cycle_subset = cycle_group_table[cycle_group_table["Tw"] == Tw]
        table = compute_cycle_pc1_moving_average(
            state_subset,
            cycle_subset,
            state_recovery_time_for_figD=state_recovery_time_for_figD,
            window_size=window_size,
        )
        table.insert(0, "Tw", Tw)
        table["state_recovery_time"] = state_recovery_time_for_figD
        tables.append(table)

    if not tables:
        return pd.DataFrame(
            columns=[
                "Tw",
                "PC1_window_center",
                "cycle_group",
                "mean_cycle_activation",
                "sem_cycle_activation",
                "n_cells_in_window",
                "window_size",
                "state_recovery_time",
            ]
        )
    return pd.concat(tables, ignore_index=True)


def run_final_state_analysis(simulation_data, analysis_params, recovery_dynamics=None):
    print("[analysis] building feature matrix", flush=True)
    X_features, feature_metadata = build_spin_feature_matrix(
        simulation_data, analysis_params.get("feature_mode", "selected_snapshots")
    )
    sourcefig2_path = analysis_params["sourcefig2_path"]
    print("[analysis] loading tail fraction table", flush=True)
    tail_fraction = load_tail_fraction_table(
        sourcefig2_path, analysis_params["waiting_times"]
    )
    print("[analysis] running PCA", flush=True)
    pca_scores, pca_explained = run_pca(
        X_features,
        analysis_params["pca_components"],
        method=analysis_params.get("pca_method", "full"),
    )
    pc_columns = [col for col in pca_scores.columns if col.startswith("PC")]
    X_embedding = pca_scores[pc_columns].to_numpy()
    print("[analysis] running UMAP", flush=True)
    umap_scores = run_umap(
        X_embedding,
        analysis_params["random_seed"],
        n_neighbors=analysis_params.get("umap_n_neighbors", 20),
        min_dist=analysis_params.get("umap_min_dist", 0.2),
    )
    print("[analysis] running clustering", flush=True)
    cluster_labels = run_clustering(
        X_embedding,
        analysis_params["n_clusters"],
        analysis_params["random_seed"],
    )
    labeled_metadata = assign_presister_like_by_tail_fraction(
        simulation_data["metadata"], tail_fraction
    )
    cell_state_table = build_cell_state_table(
        feature_metadata, pca_scores, umap_scores, cluster_labels, labeled_metadata
    )
    state_for_cluster = analysis_params.get(
        "state_recovery_time_for_cluster_summary", 0
    )
    cluster_summary = summarize_cluster_by_Tw(cell_state_table, state_for_cluster)
    recovery_by_cluster = summarize_recovery_time_by_cluster(
        cell_state_table, state_for_cluster
    )
    if recovery_dynamics is None:
        print("[analysis] computing recovery dynamics from merged table", flush=True)
        recovery_dynamics = compute_recovery_dynamics_by_Tw(
            simulation_data["magnetization"], simulation_data["metadata"]
        )
    cycle_group_features = simulation_data["cycle_group_features"]
    print("[analysis] computing cycle PC1 moving average", flush=True)
    cycle_pc1 = compute_cycle_pc1_moving_average(
        cell_state_table,
        cycle_group_features,
        analysis_params.get("state_recovery_time_for_figD", 0),
        analysis_params.get("figD_window_size", 100),
    )
    return {
        "tail_fraction_by_Tw": tail_fraction,
        "recovery_dynamics_by_Tw": recovery_dynamics,
        "cell_state_table": cell_state_table,
        "pca_scores": pca_scores,
        "pca_explained_variance": pca_explained,
        "umap_scores": umap_scores,
        "cluster_summary_by_Tw": cluster_summary,
        "recovery_time_by_cluster": recovery_by_cluster,
        "cycle_group_features": cycle_group_features,
        "cycle_pc1_moving_average": cycle_pc1,
    }

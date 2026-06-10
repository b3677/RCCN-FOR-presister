import json

import numpy as np
import pandas as pd


def ensure_output_dirs(paths):
    for path in paths.values():
        path.mkdir(parents=True, exist_ok=True)


def save_params(params, output_dir):
    with (output_dir / "params.json").open("w", encoding="utf-8") as handle:
        json.dump(params, handle, indent=2)


def save_simulation_outputs(batch_result, paths):
    simulation_dir = paths["simulation"]
    simulation_dir.mkdir(parents=True, exist_ok=True)

    batch_result["metadata"].to_csv(simulation_dir / "metadata.csv", index=False)
    batch_result["magnetization"].to_csv(
        simulation_dir / "magnetization.csv", index=False
    )
    np.save(simulation_dir / "spin_release.npy", batch_result["spin_release"])
    np.save(
        simulation_dir / "spin_early_recovery.npy",
        batch_result["spin_early_recovery"],
    )
    if "selected_spin_snapshots" in batch_result:
        np.save(
            simulation_dir / "selected_spin_snapshots.npy",
            batch_result["selected_spin_snapshots"],
        )
        batch_result["snapshot_metadata"].to_csv(
            simulation_dir / "snapshot_metadata.csv", index=False
        )
        batch_result["cycle_group_features"].to_csv(
            simulation_dir / "cycle_group_features.csv", index=False
        )


def load_simulation_outputs(paths):
    simulation_dir = paths["simulation"]
    result = {
        "metadata": pd.read_csv(simulation_dir / "metadata.csv"),
        "magnetization": pd.read_csv(simulation_dir / "magnetization.csv"),
        "spin_release": np.load(simulation_dir / "spin_release.npy"),
        "spin_early_recovery": np.load(simulation_dir / "spin_early_recovery.npy"),
    }
    selected_path = simulation_dir / "selected_spin_snapshots.npy"
    if selected_path.exists():
        result["selected_spin_snapshots"] = np.load(selected_path)
        result["snapshot_metadata"] = pd.read_csv(
            simulation_dir / "snapshot_metadata.csv"
        )
        result["cycle_group_features"] = pd.read_csv(
            simulation_dir / "cycle_group_features.csv"
        )
    return result


def save_final_simulation_outputs(batch_result, paths):
    simulation_dir = paths["final_simulation"]
    simulation_dir.mkdir(parents=True, exist_ok=True)
    batch_result["metadata"].to_csv(simulation_dir / "metadata.csv", index=False)
    batch_result["magnetization"].to_csv(
        simulation_dir / "magnetization.csv", index=False
    )
    np.save(simulation_dir / "spin_release.npy", batch_result["spin_release"])
    np.save(
        simulation_dir / "spin_early_recovery.npy",
        batch_result["spin_early_recovery"],
    )
    np.save(
        simulation_dir / "selected_spin_snapshots.npy",
        batch_result["selected_spin_snapshots"],
    )
    batch_result["snapshot_metadata"].to_csv(
        simulation_dir / "snapshot_metadata.csv", index=False
    )
    batch_result["cycle_group_features"].to_csv(
        simulation_dir / "cycle_group_features.csv", index=False
    )


def load_final_simulation_outputs(paths):
    simulation_dir = paths["final_simulation"]
    return {
        "metadata": pd.read_csv(simulation_dir / "metadata.csv"),
        "magnetization": pd.read_csv(simulation_dir / "magnetization.csv"),
        "spin_release": np.load(simulation_dir / "spin_release.npy"),
        "spin_early_recovery": np.load(simulation_dir / "spin_early_recovery.npy"),
        "selected_spin_snapshots": np.load(
            simulation_dir / "selected_spin_snapshots.npy"
        ),
        "snapshot_metadata": pd.read_csv(simulation_dir / "snapshot_metadata.csv"),
        "cycle_group_features": pd.read_csv(
            simulation_dir / "cycle_group_features.csv"
        ),
    }


def save_final_analysis_outputs(analysis_result, paths):
    analysis_dir = paths["final_analysis"]
    analysis_dir.mkdir(parents=True, exist_ok=True)
    filenames = {
        "tail_fraction_by_Tw": "tail_fraction_by_Tw.csv",
        "recovery_dynamics_by_Tw": "recovery_dynamics_by_Tw.csv",
        "cell_state_table": "cell_state_table.csv",
        "pca_scores": "pca_scores.csv",
        "pca_explained_variance": "pca_explained_variance.csv",
        "umap_scores": "umap_scores.csv",
        "cluster_summary_by_Tw": "cluster_summary_by_Tw.csv",
        "recovery_time_by_cluster": "recovery_time_by_cluster.csv",
        "cycle_group_features": "cycle_group_features.csv",
        "cycle_pc1_moving_average": "cycle_pc1_moving_average.csv",
    }
    for key, filename in filenames.items():
        if key in analysis_result:
            analysis_result[key].to_csv(analysis_dir / filename, index=False)


def load_final_analysis_outputs(paths):
    analysis_dir = paths["final_analysis"]
    filenames = {
        "tail_fraction_by_Tw": "tail_fraction_by_Tw.csv",
        "recovery_dynamics_by_Tw": "recovery_dynamics_by_Tw.csv",
        "cell_state_table": "cell_state_table.csv",
        "pca_scores": "pca_scores.csv",
        "pca_explained_variance": "pca_explained_variance.csv",
        "umap_scores": "umap_scores.csv",
        "cluster_summary_by_Tw": "cluster_summary_by_Tw.csv",
        "recovery_time_by_cluster": "recovery_time_by_cluster.csv",
        "cycle_group_features": "cycle_group_features.csv",
        "cycle_pc1_moving_average": "cycle_pc1_moving_average.csv",
    }
    return {
        key: pd.read_csv(analysis_dir / filename)
        for key, filename in filenames.items()
        if (analysis_dir / filename).exists()
    }

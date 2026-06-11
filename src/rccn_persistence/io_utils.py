import json
from datetime import datetime, timezone
from pathlib import Path

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


CHECKPOINT_FILES = {
    "metadata": "metadata.csv",
    "magnetization": "magnetization.csv",
    "spin_release": "spin_release.npy",
    "spin_early_recovery": "spin_early_recovery.npy",
    "selected_spin_snapshots": "selected_spin_snapshots.npy",
    "snapshot_metadata": "snapshot_metadata.csv",
    "cycle_group_features": "cycle_group_features.csv",
}

CHECKPOINT_PARAM_KEYS = [
    "n_runs",
    "num_spins",
    "init_time",
    "relax_time",
    "gamma",
    "H_init",
    "H_stress",
    "H_relax",
    "max_cycle_length",
    "selected_recovery_times",
    "random_seed",
]


def _tw_checkpoint_dir(checkpoint_root, Tw):
    return Path(checkpoint_root) / f"Tw_{int(Tw)}"


def _checkpoint_run_metadata(Tw, params, worker_count=None):
    metadata = {
        "Tw": int(Tw),
        "finished_at": datetime.now(timezone.utc).isoformat(),
        "output_files": list(CHECKPOINT_FILES.values()),
    }
    for key in CHECKPOINT_PARAM_KEYS:
        if key in params:
            metadata[key] = params[key]
    if worker_count is not None:
        metadata["worker_count"] = int(worker_count)
    return metadata


def save_waiting_time_checkpoint(result, checkpoint_root, Tw, params, worker_count=None):
    tw_dir = _tw_checkpoint_dir(checkpoint_root, Tw)
    tw_dir.mkdir(parents=True, exist_ok=True)

    done_path = tw_dir / "done.json"
    tmp_done_path = tw_dir / "done.tmp.json"
    if done_path.exists():
        done_path.unlink()
    if tmp_done_path.exists():
        tmp_done_path.unlink()

    result["metadata"].to_csv(tw_dir / CHECKPOINT_FILES["metadata"], index=False)
    result["magnetization"].to_csv(
        tw_dir / CHECKPOINT_FILES["magnetization"], index=False
    )
    np.save(tw_dir / CHECKPOINT_FILES["spin_release"], result["spin_release"])
    np.save(
        tw_dir / CHECKPOINT_FILES["spin_early_recovery"],
        result["spin_early_recovery"],
    )
    np.save(
        tw_dir / CHECKPOINT_FILES["selected_spin_snapshots"],
        result["selected_spin_snapshots"],
    )
    result["snapshot_metadata"].to_csv(
        tw_dir / CHECKPOINT_FILES["snapshot_metadata"], index=False
    )
    result["cycle_group_features"].to_csv(
        tw_dir / CHECKPOINT_FILES["cycle_group_features"], index=False
    )

    done_metadata = _checkpoint_run_metadata(Tw, params, worker_count=worker_count)
    with tmp_done_path.open("w", encoding="utf-8") as handle:
        json.dump(done_metadata, handle, indent=2)
    tmp_done_path.replace(done_path)


def load_waiting_time_checkpoint(checkpoint_root, Tw):
    tw_dir = _tw_checkpoint_dir(checkpoint_root, Tw)
    return {
        "metadata": pd.read_csv(tw_dir / CHECKPOINT_FILES["metadata"]),
        "magnetization": pd.read_csv(tw_dir / CHECKPOINT_FILES["magnetization"]),
        "spin_release": np.load(tw_dir / CHECKPOINT_FILES["spin_release"]),
        "spin_early_recovery": np.load(
            tw_dir / CHECKPOINT_FILES["spin_early_recovery"]
        ),
        "selected_spin_snapshots": np.load(
            tw_dir / CHECKPOINT_FILES["selected_spin_snapshots"]
        ),
        "snapshot_metadata": pd.read_csv(
            tw_dir / CHECKPOINT_FILES["snapshot_metadata"]
        ),
        "cycle_group_features": pd.read_csv(
            tw_dir / CHECKPOINT_FILES["cycle_group_features"]
        ),
    }


def is_waiting_time_checkpoint_complete(checkpoint_root, Tw, params):
    tw_dir = _tw_checkpoint_dir(checkpoint_root, Tw)
    done_path = tw_dir / "done.json"
    if not done_path.exists():
        return False

    for filename in CHECKPOINT_FILES.values():
        if not (tw_dir / filename).exists():
            return False

    with done_path.open("r", encoding="utf-8") as handle:
        done_metadata = json.load(handle)

    expected_metadata = _checkpoint_run_metadata(Tw, params)
    for key in ["Tw", *CHECKPOINT_PARAM_KEYS]:
        if key in expected_metadata and done_metadata.get(key) != expected_metadata[key]:
            return False
    return True


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

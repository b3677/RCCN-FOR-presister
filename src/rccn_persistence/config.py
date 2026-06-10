from pathlib import Path


def make_default_params():
    """Return the first-version RCCN simulation parameters."""
    return {
        "num_spins": 2**14,
        "init_time": 2000,
        "relax_time": 9000,
        "waiting_times": [20, 40, 80, 160, 320, 640, 1280, 3000],
        "gamma": 1.5,
        "H_init": 0.0,
        "H_stress": 0.8,
        "H_relax": 0.0,
        "n_runs": 20,
        "max_cycle_length": 2500,
        "early_recovery_delta": 100,
        "baseline_window": 1000,
        "save_full_trajectory": False,
        "different_initial_conditions": False,
        "pca_components": 10,
        "n_clusters": 3,
        "random_seed": 1,
    }


def make_debug_params():
    """Small parameters for checking the full pipeline quickly."""
    params = make_default_params()
    params.update(
        {
            "num_spins": 512,
            "n_runs": 3,
            "waiting_times": [20, 40],
            "random_seed": 1,
        }
    )
    return params


def make_final_project_params():
    """Return parameters for the final RCCN figure pipeline."""
    params = make_default_params()
    params.update(
        {
            "waiting_times": [0, 195, 488, 1346, 1500],
            "n_runs": 900,
            "selected_recovery_times": [0, 20, 120],
            "early_recovery_delta": 20,
            "pca_components": 10,
            "n_clusters": 3,
            "feature_mode": "selected_snapshots",
            "state_recovery_time_for_cluster_summary": 0,
            "state_recovery_time_for_figE": 0,
            "state_recovery_time_for_figD": 0,
            "figD_window_size": 100,
            "umap_n_neighbors": 20,
            "umap_min_dist": 0.2,
            "sourcefig2_path": str(Path("data") / "sourcefig2.xlsx"),
            "random_seed": 1,
        }
    )
    return params


def make_output_paths(project_root):
    project_root = Path(project_root)
    return {
        "simulation": project_root / "output" / "rccn_simulation",
        "clustering": project_root / "output" / "spin_clustering",
        "figures": project_root / "output" / "figures",
    }


def make_final_output_paths(project_root):
    project_root = Path(project_root)
    return {
        "final_simulation": project_root / "output" / "final_simulation",
        "final_analysis": project_root / "output" / "final_analysis",
        "final_figures": project_root / "output" / "final_figures",
    }

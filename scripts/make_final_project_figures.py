import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from rccn_persistence.config import make_final_output_paths, make_final_project_params
from rccn_persistence.io_utils import ensure_output_dirs, load_final_analysis_outputs
from rccn_persistence.plotting import (
    plot_figA_recovery_dynamics,
    plot_figB_umap_by_Tw_recovery_time,
    plot_figB_umap_recovery_time_exploration,
    plot_figC_cluster_occupancy_and_lag,
    plot_figD_cycle_groups_along_PC1,
    plot_figE_presister_like_pca_umap,
)


MAIN_FIGB_RECOVERY_TIMES = [0, 500, 2000]
EXPLORATORY_FIGB_RECOVERY_TIMES = [0, 250, 500, 1000, 2000, 4000]


def require_recovery_times(cell_state_table, required_times, figure_name):
    available = sorted(
        int(time) for time in cell_state_table["state_recovery_time"].dropna().unique()
    )
    missing = sorted(set(required_times) - set(available))
    if missing:
        raise ValueError(
            f"{figure_name} needs state_recovery_time={required_times}, "
            f"but the current analysis table only has {available}. "
            "Rerun the final simulation and final state analysis with "
            "selected_recovery_times=[0, 250, 500, 1000, 2000, 4000]."
        )


def main():
    params = make_final_project_params()
    paths = make_final_output_paths(PROJECT_ROOT)
    ensure_output_dirs(paths)
    params_path = paths["final_simulation"] / "params.json"
    if params_path.exists():
        with params_path.open("r", encoding="utf-8") as handle:
            params.update(json.load(handle))

    analysis = load_final_analysis_outputs(paths)
    figure_dir = paths["final_figures"]
    figure_dir.mkdir(parents=True, exist_ok=True)
    require_recovery_times(
        analysis["cell_state_table"], MAIN_FIGB_RECOVERY_TIMES, "Main Fig. B"
    )
    require_recovery_times(
        analysis["cell_state_table"],
        EXPLORATORY_FIGB_RECOVERY_TIMES,
        "Exploratory Fig. B",
    )

    plot_figA_recovery_dynamics(
        analysis["recovery_dynamics_by_Tw"],
        figure_dir / "figA_rccn_ageing_reproduction.png",
    )
    plot_figC_cluster_occupancy_and_lag(
        analysis["cluster_summary_by_Tw"],
        analysis["cell_state_table"],
        figure_dir / "figC_cluster_occupancy_lag_by_cluster.png",
        params["state_recovery_time_for_cluster_summary"],
    )
    plot_figE_presister_like_pca_umap(
        analysis["cell_state_table"],
        figure_dir / "figE_presister_like_PCA_UMAP.png",
        params["state_recovery_time_for_figE"],
    )
    plot_figB_umap_by_Tw_recovery_time(
        analysis["cell_state_table"],
        analysis["tail_fraction_by_Tw"],
        figure_dir / "figB_umap_by_Tw_recovery_time.png",
        selected_recovery_times=MAIN_FIGB_RECOVERY_TIMES,
    )
    plot_figB_umap_recovery_time_exploration(
        analysis["cell_state_table"],
        analysis["tail_fraction_by_Tw"],
        figure_dir / "figB_umap_recovery_time_exploration_6color.png",
    )
    plot_figD_cycle_groups_along_PC1(
        analysis["cycle_pc1_moving_average"],
        analysis["cell_state_table"],
        figure_dir / "figD_cycle_groups_along_PC1.png",
        params["state_recovery_time_for_figD"],
    )
    print(f"[done] final figures: {figure_dir}")


if __name__ == "__main__":
    main()

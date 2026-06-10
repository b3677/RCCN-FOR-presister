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
    plot_figC_cluster_occupancy_and_lag,
    plot_figD_cycle_groups_along_PC1,
    plot_figE_presister_like_pca_umap,
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

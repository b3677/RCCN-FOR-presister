import json
import sys
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from rccn_persistence.config import make_final_output_paths, make_final_project_params
from rccn_persistence.io_utils import ensure_output_dirs, load_final_analysis_outputs
from rccn_persistence.observables import compute_recovery_survival_to_zero_by_Tw
from rccn_persistence.plotting import (
    plot_figA_recovery_survival_semilog_loglog,
    plot_figB_umap_by_Tw_recovery_time,
    plot_figB_umap_recovery_time_exploration,
    plot_figC_cluster_occupancy_and_lag,
    plot_figD_cycle_groups_along_PC1,
    plot_figE_presister_like_pca_umap,
)
from rccn_persistence.spin_analysis import compute_cycle_pc1_moving_average_by_Tw


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
    metadata = pd.read_csv(paths["final_simulation"] / "metadata.csv")
    require_recovery_times(
        analysis["cell_state_table"], MAIN_FIGB_RECOVERY_TIMES, "Main Fig. B"
    )
    require_recovery_times(
        analysis["cell_state_table"],
        EXPLORATORY_FIGB_RECOVERY_TIMES,
        "Exploratory Fig. B",
    )

    redraw_dir = PROJECT_ROOT / "output" / "redraw0609result"
    redraw_dir.mkdir(parents=True, exist_ok=True)

    recovery_survival = compute_recovery_survival_to_zero_by_Tw(
        paths["final_simulation"] / "magnetization.csv",
        metadata,
        params["relax_time"],
    )
    recovery_survival.to_csv(
        redraw_dir / "recovery_survival_M0_by_Tw.csv", index=False
    )

    cycle_pc1_by_Tw = compute_cycle_pc1_moving_average_by_Tw(
        analysis["cell_state_table"],
        analysis["cycle_group_features"],
        params["state_recovery_time_for_figD"],
        params["figD_window_size"],
    )
    cycle_pc1_by_Tw.to_csv(
        redraw_dir / "cycle_pc1_moving_average_by_Tw.csv", index=False
    )

    plot_figA_recovery_survival_semilog_loglog(
        recovery_survival,
        redraw_dir / "figA_rccn_ageing_reproduction.png",
    )
    plot_figA_recovery_survival_semilog_loglog(
        recovery_survival,
        redraw_dir / "figA_recovery_survival_M0_semilog_loglog.png",
    )

    plot_figB_umap_by_Tw_recovery_time(
        analysis["cell_state_table"],
        analysis["tail_fraction_by_Tw"],
        redraw_dir / "figB_umap_by_Tw_recovery_time.png",
        selected_recovery_times=MAIN_FIGB_RECOVERY_TIMES,
    )
    plot_figB_umap_recovery_time_exploration(
        analysis["cell_state_table"],
        analysis["tail_fraction_by_Tw"],
        redraw_dir / "figB_umap_recovery_time_exploration_6color.png",
    )
    plot_figC_cluster_occupancy_and_lag(
        analysis["cluster_summary_by_Tw"],
        analysis["cell_state_table"],
        redraw_dir / "figC_cluster_occupancy_lag_by_cluster.png",
        params["state_recovery_time_for_cluster_summary"],
    )
    plot_figE_presister_like_pca_umap(
        analysis["cell_state_table"],
        redraw_dir / "figE_presister_like_PCA_UMAP.png",
        params["state_recovery_time_for_figE"],
    )
    plot_figD_cycle_groups_along_PC1(
        analysis["cycle_pc1_moving_average"],
        analysis["cell_state_table"],
        redraw_dir / "figD_cycle_groups_along_PC1.png",
        params["state_recovery_time_for_figD"],
        title_suffix="all Tw",
    )
    plot_figD_cycle_groups_along_PC1(
        analysis["cycle_pc1_moving_average"],
        analysis["cell_state_table"],
        redraw_dir / "figD_cycle_groups_along_PC1_mixed.png",
        params["state_recovery_time_for_figD"],
        title_suffix="all Tw",
    )

    for Tw in sorted(analysis["cell_state_table"]["Tw"].dropna().unique()):
        cycle_table = cycle_pc1_by_Tw[cycle_pc1_by_Tw["Tw"] == Tw]
        cell_table = analysis["cell_state_table"][
            analysis["cell_state_table"]["Tw"] == Tw
        ]
        plot_figD_cycle_groups_along_PC1(
            cycle_table,
            cell_table,
            redraw_dir / f"figD_cycle_groups_along_PC1_Tw{int(Tw)}.png",
            params["state_recovery_time_for_figD"],
            title_suffix=f"Tw={int(Tw)} min",
        )

    print(f"[done] redraw figures and tables: {redraw_dir}")


if __name__ == "__main__":
    main()

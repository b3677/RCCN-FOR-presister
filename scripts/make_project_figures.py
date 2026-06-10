import sys
from pathlib import Path
import json

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from rccn_persistence.config import make_default_params, make_output_paths
from rccn_persistence.observables import compute_survival_by_Tw, summarize_fate_by_Tw
from rccn_persistence.plotting import (
    plot_cluster_occupancy,
    plot_fate_fraction_by_Tw,
    plot_pca_by_cluster,
    plot_pca_by_fate,
    plot_pca_by_column,
    plot_survival_by_Tw,
)


def main():
    params = make_default_params()
    paths = make_output_paths(PROJECT_ROOT)
    paths["figures"].mkdir(parents=True, exist_ok=True)

    params_path = paths["simulation"] / "params.json"
    if params_path.exists():
        with params_path.open("r", encoding="utf-8") as handle:
            params.update(json.load(handle))

    metadata = pd.read_csv(paths["simulation"] / "metadata.csv")
    pca_scores = pd.read_csv(paths["clustering"] / "pca_scores.csv")
    cluster_labels = pd.read_csv(paths["clustering"] / "cluster_labels.csv")
    occupancy = pd.read_csv(paths["clustering"] / "cluster_occupancy_by_Tw.csv")

    survival = compute_survival_by_Tw(metadata, params["relax_time"])
    fate_occupancy = summarize_fate_by_Tw(metadata)
    plot_survival_by_Tw(
        survival, paths["figures"] / "fig1_recovery_survival_by_Tw.png"
    )
    plot_pca_by_column(
        pca_scores, metadata, "Tw", paths["figures"] / "fig2_spin_pca_by_Tw.png"
    )
    plot_pca_by_cluster(
        pca_scores,
        cluster_labels,
        paths["figures"] / "fig3_spin_pca_by_cluster.png",
    )
    plot_pca_by_column(
        pca_scores,
        metadata,
        "recovery_time",
        paths["figures"] / "fig4_spin_pca_by_recovery_time.png",
    )
    plot_cluster_occupancy(
        occupancy, paths["figures"] / "fig5_cluster_occupancy_by_Tw.png"
    )
    plot_pca_by_fate(
        pca_scores,
        metadata,
        paths["figures"] / "fig6_spin_pca_by_regrowth_vs_persister.png",
    )
    plot_fate_fraction_by_Tw(
        fate_occupancy,
        paths["figures"] / "fig7_regrowth_vs_persister_fraction_by_Tw.png",
    )
    print(f"[done] figures: {paths['figures']}")


if __name__ == "__main__":
    main()

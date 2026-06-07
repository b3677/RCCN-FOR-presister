import argparse
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from rccn_persistence.config import make_default_params, make_output_paths
from rccn_persistence.io_utils import ensure_output_dirs, load_simulation_outputs
from rccn_persistence.spin_analysis import run_spin_clustering_analysis


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--n-components", type=int)
    parser.add_argument("--n-clusters", type=int)
    args = parser.parse_args()

    params = make_default_params()
    if args.n_components is not None:
        params["pca_components"] = args.n_components
    if args.n_clusters is not None:
        params["n_clusters"] = args.n_clusters

    paths = make_output_paths(PROJECT_ROOT)
    ensure_output_dirs(paths)
    simulation_data = load_simulation_outputs(paths)
    analysis_result = run_spin_clustering_analysis(simulation_data, params)

    output_dir = paths["clustering"]
    analysis_result["pca_scores"].to_csv(output_dir / "pca_scores.csv", index=False)
    analysis_result["explained_variance"].to_csv(
        output_dir / "pca_explained_variance.csv", index=False
    )
    analysis_result["cluster_labels"].to_csv(
        output_dir / "cluster_labels.csv", index=False
    )
    analysis_result["cluster_occupancy_by_Tw"].to_csv(
        output_dir / "cluster_occupancy_by_Tw.csv", index=False
    )
    analysis_result["recovery_time_by_cluster"].to_csv(
        output_dir / "recovery_time_by_cluster.csv", index=False
    )
    print(f"[done] clustering outputs: {output_dir}")


if __name__ == "__main__":
    main()


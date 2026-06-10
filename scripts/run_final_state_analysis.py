import argparse
import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from rccn_persistence.config import make_final_output_paths, make_final_project_params
from rccn_persistence.io_utils import (
    ensure_output_dirs,
    load_final_simulation_outputs,
    save_final_analysis_outputs,
)
from rccn_persistence.spin_analysis import run_final_state_analysis


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--n-clusters", type=int)
    parser.add_argument("--pca-components", type=int)
    parser.add_argument("--figD-window-size", type=int)
    args = parser.parse_args()

    params = make_final_project_params()
    paths = make_final_output_paths(PROJECT_ROOT)
    ensure_output_dirs(paths)

    params_path = paths["final_simulation"] / "params.json"
    if params_path.exists():
        with params_path.open("r", encoding="utf-8") as handle:
            params.update(json.load(handle))

    if args.n_clusters is not None:
        params["n_clusters"] = args.n_clusters
    if args.pca_components is not None:
        params["pca_components"] = args.pca_components
    if args.figD_window_size is not None:
        params["figD_window_size"] = args.figD_window_size

    sourcefig2_path = Path(params["sourcefig2_path"])
    if not sourcefig2_path.is_absolute():
        sourcefig2_path = PROJECT_ROOT / sourcefig2_path
    params["sourcefig2_path"] = sourcefig2_path

    simulation_data = load_final_simulation_outputs(paths)
    analysis_result = run_final_state_analysis(simulation_data, params)
    save_final_analysis_outputs(analysis_result, paths)
    print(f"[done] final analysis outputs: {paths['final_analysis']}")


if __name__ == "__main__":
    main()

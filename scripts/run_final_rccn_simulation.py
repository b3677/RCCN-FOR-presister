import argparse
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from rccn_persistence.config import make_final_output_paths, make_final_project_params
from rccn_persistence.io_utils import (
    ensure_output_dirs,
    save_final_simulation_outputs,
    save_params,
)
from rccn_persistence.simulation import run_batch


def apply_smoke_overrides(params):
    params.update(
        {
            "num_spins": 64,
            "n_runs": 2,
            "waiting_times": [0, 488, 1346],
            "init_time": 20,
            "relax_time": 140,
            "baseline_window": 10,
            "max_cycle_length": 20,
            "selected_recovery_times": [0, 20, 120],
            "pca_components": 5,
            "figD_window_size": 4,
        }
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--preset", choices=["smoke", "final"], default="final")
    parser.add_argument("--n-runs", type=int)
    parser.add_argument("--num-spins", type=int)
    parser.add_argument("--waiting-times", nargs="*", type=int)
    parser.add_argument("--init-time", type=int)
    parser.add_argument("--relax-time", type=int)
    parser.add_argument("--baseline-window", type=int)
    parser.add_argument("--max-cycle-length", type=int)
    parser.add_argument("--selected-recovery-times", nargs="*", type=int)
    parser.add_argument("--seed", type=int)
    args = parser.parse_args()

    params = make_final_project_params()
    if args.preset == "smoke":
        apply_smoke_overrides(params)

    if args.n_runs is not None:
        params["n_runs"] = args.n_runs
    if args.num_spins is not None:
        params["num_spins"] = args.num_spins
    if args.waiting_times:
        params["waiting_times"] = args.waiting_times
    if args.init_time is not None:
        params["init_time"] = args.init_time
    if args.relax_time is not None:
        params["relax_time"] = args.relax_time
    if args.baseline_window is not None:
        params["baseline_window"] = args.baseline_window
    if args.max_cycle_length is not None:
        params["max_cycle_length"] = args.max_cycle_length
    if args.selected_recovery_times:
        params["selected_recovery_times"] = args.selected_recovery_times
    if args.seed is not None:
        params["random_seed"] = args.seed

    max_snapshot_time = max(params["selected_recovery_times"])
    if params["relax_time"] <= max_snapshot_time:
        raise ValueError("relax_time must be larger than the largest selected snapshot")

    paths = make_final_output_paths(PROJECT_ROOT)
    ensure_output_dirs(paths)
    save_params(params, paths["final_simulation"])

    batch_result = run_batch(params)
    save_final_simulation_outputs(batch_result, paths)
    print(f"[done] final simulation outputs: {paths['final_simulation']}")


if __name__ == "__main__":
    main()

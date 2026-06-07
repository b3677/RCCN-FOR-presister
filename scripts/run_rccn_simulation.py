import argparse
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from rccn_persistence.config import make_debug_params, make_default_params, make_output_paths
from rccn_persistence.io_utils import ensure_output_dirs, save_params, save_simulation_outputs
from rccn_persistence.simulation import run_batch


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--preset", choices=["debug", "default"], default="debug")
    parser.add_argument("--n-runs", type=int)
    parser.add_argument("--num-spins", type=int)
    parser.add_argument("--waiting-times", nargs="*", type=int)
    parser.add_argument("--init-time", type=int)
    parser.add_argument("--relax-time", type=int)
    parser.add_argument("--early-recovery-delta", type=int)
    parser.add_argument("--baseline-window", type=int)
    parser.add_argument("--seed", type=int)
    args = parser.parse_args()

    params = make_debug_params() if args.preset == "debug" else make_default_params()
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
    if args.early_recovery_delta is not None:
        params["early_recovery_delta"] = args.early_recovery_delta
    if args.baseline_window is not None:
        params["baseline_window"] = args.baseline_window
    if args.seed is not None:
        params["random_seed"] = args.seed

    paths = make_output_paths(PROJECT_ROOT)
    ensure_output_dirs(paths)
    save_params(params, paths["simulation"])

    batch_result = run_batch(params)
    save_simulation_outputs(batch_result, paths)
    print(f"[done] simulation outputs: {paths['simulation']}")


if __name__ == "__main__":
    main()

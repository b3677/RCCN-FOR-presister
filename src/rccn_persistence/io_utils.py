import json

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


def load_simulation_outputs(paths):
    simulation_dir = paths["simulation"]
    return {
        "metadata": pd.read_csv(simulation_dir / "metadata.csv"),
        "magnetization": pd.read_csv(simulation_dir / "magnetization.csv"),
        "spin_release": np.load(simulation_dir / "spin_release.npy"),
        "spin_early_recovery": np.load(simulation_dir / "spin_early_recovery.npy"),
    }


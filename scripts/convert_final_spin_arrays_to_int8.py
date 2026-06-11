"""Maintenance utility for compacting completed final simulation spin arrays.

This script is not part of the normal final analysis pipeline. Use it only when
existing `output/result611/final_simulation` spin-state `.npy` files need to be
converted to compact `int8` storage after a completed simulation.
"""

import argparse
import sys
from pathlib import Path

import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from rccn_persistence.config import make_final_output_paths


SPIN_ARRAY_FILENAMES = [
    "spin_release.npy",
    "spin_early_recovery.npy",
    "selected_spin_snapshots.npy",
]


def is_int8_spin_array(path):
    array = np.load(path, mmap_mode="r")
    result = array.dtype == np.int8
    close_memmap(array)
    return result


def close_memmap(array):
    mmap = getattr(array, "_mmap", None)
    if mmap is not None:
        mmap.close()


def convert_one(path, backup_original=True):
    source = Path(path)
    if not source.exists():
        raise FileNotFoundError(source)

    array = np.load(source, mmap_mode="r")
    if array.dtype == np.int8:
        print(f"[skip] already int8: {source}")
        return None

    unique_values = np.unique(array)
    if not set(unique_values.tolist()).issubset({-1, 1}):
        raise ValueError(
            f"{source} contains values outside expected spin states -1/+1: "
            f"{unique_values[:10]}"
        )

    tmp_path = source.with_name(source.stem + ".int8.tmp.npy")
    backup_path = source.with_name(source.name + ".int64.bak")

    if backup_original and backup_path.exists():
        raise FileExistsError(f"backup output already exists: {backup_path}")

    if tmp_path.exists():
        print(f"[resume] validating existing temporary file: {tmp_path}")
    else:
        print(
            f"[convert] {source.name}: {array.dtype}, shape={array.shape} -> int8",
            flush=True,
        )
        np.save(tmp_path, array.astype(np.int8, copy=False))

    converted = np.load(tmp_path, mmap_mode="r")
    if converted.dtype != np.int8:
        raise ValueError(f"converted file is not int8: {tmp_path}")
    if converted.shape != array.shape:
        raise ValueError(f"shape mismatch after conversion: {tmp_path}")
    close_memmap(converted)
    close_memmap(array)
    del converted
    del array

    if backup_original:
        source.replace(backup_path)
        tmp_path.replace(source)
        print(f"[done] replaced {source}; backup kept at {backup_path}")
        return backup_path

    final_path = source.with_name(source.stem + ".int8.npy")
    if final_path.exists():
        raise FileExistsError(f"converted output already exists: {final_path}")
    tmp_path.replace(final_path)
    print(f"[done] wrote {final_path}; original kept at {source}")
    return final_path


def convert_directory(directory, backup_original=True):
    backups = []
    for filename in SPIN_ARRAY_FILENAMES:
        path = Path(directory) / filename
        if path.exists():
            backup_or_output = convert_one(path, backup_original=backup_original)
            if backup_or_output is not None:
                backups.append(backup_or_output)
    return backups


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--include-checkpoints",
        action="store_true",
        help="Also convert per-Tw checkpoint spin arrays.",
    )
    parser.add_argument(
        "--no-backup",
        action="store_true",
        help="Write .int8.npy files and keep originals in place.",
    )
    args = parser.parse_args()

    paths = make_final_output_paths(PROJECT_ROOT)
    simulation_dir = paths["final_simulation"]
    backup_original = not args.no_backup

    produced = []
    produced.extend(convert_directory(simulation_dir, backup_original=backup_original))

    if args.include_checkpoints:
        checkpoint_root = simulation_dir / "checkpoints"
        for tw_dir in sorted(checkpoint_root.glob("Tw_*")):
            if tw_dir.is_dir():
                produced.extend(
                    convert_directory(tw_dir, backup_original=backup_original)
                )

    print("")
    print("[summary] conversion complete")
    if backup_original:
        print("[summary] old large files kept as backups and can be deleted after analysis succeeds:")
    else:
        print("[summary] converted outputs written separately:")
    for path in produced:
        print(path)


if __name__ == "__main__":
    main()

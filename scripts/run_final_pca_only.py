"""Diagnostic utility for testing PCA on final spin-state features.

This script is not part of the normal final analysis pipeline. It runs PCA only
and writes diagnostic outputs under `output/result611/pca_diagnostics` by
default, without touching the official `final_analysis` tables.
"""

import argparse
import os
import sys
import time
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))


def set_thread_env(thread_count):
    value = str(int(thread_count))
    os.environ["OPENBLAS_NUM_THREADS"] = value
    os.environ["OMP_NUM_THREADS"] = value
    os.environ["NUMEXPR_NUM_THREADS"] = value


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--method", choices=["full", "incremental"], default="full")
    parser.add_argument("--components", type=int, default=10)
    parser.add_argument("--threads", type=int, default=4)
    parser.add_argument(
        "--max-rows",
        type=int,
        help="Use only the first N feature rows for a quick diagnostic run.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=PROJECT_ROOT / "output" / "result611" / "pca_diagnostics",
    )
    args = parser.parse_args()

    set_thread_env(args.threads)

    import numpy as np
    import pandas as pd
    from sklearn.decomposition import IncrementalPCA, PCA

    from rccn_persistence.config import make_final_output_paths

    paths = make_final_output_paths(PROJECT_ROOT)
    feature_path = paths["final_simulation"] / "selected_spin_snapshots.npy"
    X = np.load(feature_path, mmap_mode="r")
    if args.max_rows is not None:
        X = X[: args.max_rows]

    n_components = min(args.components, X.shape[0], X.shape[1])
    args.output_dir.mkdir(parents=True, exist_ok=True)

    print(
        f"[pca-only] method={args.method} threads={args.threads} "
        f"shape={X.shape} dtype={X.dtype} components={n_components}",
        flush=True,
    )
    start_time = time.time()

    if args.method == "full":
        print("[pca-only] converting feature matrix to float32", flush=True)
        X_float = np.asarray(X, dtype=np.float32)
        print("[pca-only] running sklearn PCA", flush=True)
        model = PCA(n_components=n_components, svd_solver="auto")
        scores = model.fit_transform(X_float)
    else:
        batch_size = max(1024, n_components * 10)
        model = IncrementalPCA(n_components=n_components, batch_size=batch_size)
        for start in range(0, X.shape[0], batch_size):
            stop = min(start + batch_size, X.shape[0])
            print(f"[pca-only] partial_fit rows {start}:{stop}", flush=True)
            model.partial_fit(np.asarray(X[start:stop], dtype=np.float32))

        chunks = []
        for start in range(0, X.shape[0], batch_size):
            stop = min(start + batch_size, X.shape[0])
            print(f"[pca-only] transform rows {start}:{stop}", flush=True)
            chunks.append(model.transform(np.asarray(X[start:stop], dtype=np.float32)))
        scores = np.vstack(chunks)

    elapsed = time.time() - start_time
    score_columns = [f"PC{i + 1}" for i in range(scores.shape[1])]
    pca_scores = pd.DataFrame(scores, columns=score_columns)
    pca_scores.insert(0, "feature_row_id", np.arange(len(pca_scores)))
    explained = pd.DataFrame(
        {
            "PC": np.arange(1, len(model.explained_variance_ratio_) + 1),
            "explained_variance_ratio": model.explained_variance_ratio_,
        }
    )

    row_label = "all" if args.max_rows is None else str(args.max_rows)
    prefix = f"{args.method}_pca_rows_{row_label}_threads_{args.threads}"
    scores_path = args.output_dir / f"{prefix}_scores.csv"
    explained_path = args.output_dir / f"{prefix}_explained_variance.csv"
    pca_scores.to_csv(scores_path, index=False)
    explained.to_csv(explained_path, index=False)

    print(f"[pca-only] done elapsed={elapsed:.1f}s", flush=True)
    print(f"[pca-only] scores: {scores_path}", flush=True)
    print(f"[pca-only] explained variance: {explained_path}", flush=True)


if __name__ == "__main__":
    main()

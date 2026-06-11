# Memory-safe final analysis refactor plan

Date: 2026-06-11

This document follows the Scientific Code Scholar / Scientific Code Refactorer style:
first clarify the scientific goal and data flow, then specify a practical refactor plan
before changing code.

## 1. Current goal

The immediate goal is to make the completed `result611` final simulation usable for
analysis without rerunning the expensive simulation.

The failed step was:

```powershell
C:\work\env\python.exe scripts\run_final_state_analysis.py
```

The simulation step completed successfully. The failure happened during
`full_final_analysis`, after the full simulation outputs had already been written.

Main constraint:

- Preserve the scientific meaning of the final run.
- Reuse existing `output/result611/final_simulation` data whenever possible.
- Avoid loading all large arrays and the 2.31 GB magnetization table into memory at once.
- Keep the code readable as scientific analysis code, not a large framework.

## 2. Current inputs and outputs

### Existing simulation inputs for analysis

The current final simulation output directory is:

```text
output/result611/final_simulation
```

Important files:

```text
metadata.csv
magnetization.csv
spin_release.npy
spin_early_recovery.npy
selected_spin_snapshots.npy
snapshot_metadata.csv
cycle_group_features.csv
params.json
```

Large files observed in this run:

```text
selected_spin_snapshots.npy  7.86 GB
magnetization.csv            2.31 GB
spin_release.npy             1.31 GB
spin_early_recovery.npy      1.31 GB
```

Per-waiting-time checkpoints also exist:

```text
output/result611/final_simulation/checkpoints/Tw_0
output/result611/final_simulation/checkpoints/Tw_195
output/result611/final_simulation/checkpoints/Tw_488
output/result611/final_simulation/checkpoints/Tw_1346
output/result611/final_simulation/checkpoints/Tw_1500
```

Each checkpoint contains the same logical outputs for one `Tw`.

### Expected final analysis outputs

Keep the current output directory stable:

```text
output/result611/final_analysis
```

Keep these output filenames stable:

```text
tail_fraction_by_Tw.csv
recovery_dynamics_by_Tw.csv
cell_state_table.csv
pca_scores.csv
pca_explained_variance.csv
umap_scores.csv
cluster_summary_by_Tw.csv
recovery_time_by_cluster.csv
cycle_group_features.csv
cycle_pc1_moving_average.csv
```

## 3. Do these three optimizations require rerunning simulation?

Short answer: no expensive scientific rerun is required for the first rescue pass.

Detailed answer:

1. `run_final_state_analysis.py` should not load all simulation outputs at once.

   This does not require rerunning simulation. It only changes how existing files are
   loaded during analysis.

2. Save `selected_spin_snapshots.npy`, `spin_release.npy`, and
   `spin_early_recovery.npy` as `int8` instead of default `int64`.

   This has two meanings:

   - For future simulations: change the save logic so future output files are smaller.
     This does not help the already-written large files unless they are converted.
   - For the current completed run: existing `.npy` files can be converted from `int64`
     to `int8` without rerunning the simulation, because spin values are only `-1/+1`.
     This is a data-format conversion, not a new scientific simulation.

   Recommended immediate strategy:

   - Do not require conversion before the first analysis rescue attempt.
   - Use `np.load(..., mmap_mode="r")` for current large arrays.
   - Add an optional conversion script or function later if disk/memory pressure remains high.

3. Analyze `magnetization.csv` by `Tw` checkpoint chunks instead of reading the merged
   2.31 GB CSV.

   This does not require rerunning simulation. The checkpoint magnetization files already
   exist and can be read one waiting time at a time.

## 4. Scientific meaning of the changes

These changes should not alter the biological or physical model.

They only change:

- how large output files are loaded;
- whether spin arrays are stored as compact integers;
- whether recovery dynamics are computed from one merged CSV or from equivalent
  per-`Tw` checkpoint CSV files.

The analysis should preserve:

- same `waiting_times`;
- same `n_runs`;
- same `num_spins`;
- same selected recovery snapshots;
- same PCA/UMAP/clustering assumptions unless explicitly changed later.

Potential scientific change to avoid in this first pass:

- Do not randomly subsample spin features yet.
- Do not reduce `n_runs`.
- Do not change `pca_components`, `n_clusters`, UMAP parameters, or tail-fraction logic.

If memory still fails after this first pass, feature subsampling can be proposed as a
second-stage scientific/visualization compromise, but it should be documented explicitly.

## 5. Current failure hypothesis

The analysis log files were empty:

```text
full_final_analysis.stdout.log
full_final_analysis.stderr.log
```

The process exited with:

```text
exit_code=-1066598273
```

Because there was no Python traceback, the likely failure mode is not a normal Python
exception. The most likely causes are:

- memory pressure while loading `magnetization.csv` plus multiple large `.npy` files;
- native-library crash during conversion of the spin feature matrix to floating point;
- native-library crash during PCA/UMAP after a very large allocation.

The current code path is:

```text
scripts/run_final_state_analysis.py
  -> load_final_simulation_outputs(paths)
  -> run_final_state_analysis(simulation_data, params)
  -> save_final_analysis_outputs(analysis_result, paths)
```

The current loader reads everything at once:

```python
"magnetization": pd.read_csv(simulation_dir / "magnetization.csv")
"spin_release": np.load(simulation_dir / "spin_release.npy")
"spin_early_recovery": np.load(simulation_dir / "spin_early_recovery.npy")
"selected_spin_snapshots": np.load(simulation_dir / "selected_spin_snapshots.npy")
```

For the current default `feature_mode = "selected_snapshots"`, the analysis does not need
`spin_release` or `spin_early_recovery`.

## 6. Refactor plan

### File 1: `src/rccn_persistence/io_utils.py`

Add a memory-aware loader for final analysis.

Recommended function:

```text
load_final_analysis_inputs(paths, feature_mode="selected_snapshots")
```

Responsibilities:

1. Read small metadata tables:

   ```text
   metadata.csv
   snapshot_metadata.csv
   cycle_group_features.csv
   ```

2. Load only the spin array needed by `feature_mode`.

   For default `selected_snapshots`:

   ```text
   selected_spin_snapshots.npy
   ```

   Use:

   ```python
   np.load(path, mmap_mode="r")
   ```

3. Do not load:

   ```text
   spin_release.npy
   spin_early_recovery.npy
   magnetization.csv
   ```

   unless the selected feature mode truly needs them.

4. Return a dictionary compatible with `run_final_state_analysis`.

Add a checkpoint magnetization helper:

```text
iter_final_checkpoint_magnetization(paths, waiting_times)
```

Responsibilities:

1. For each `Tw`, read:

   ```text
   output/result611/final_simulation/checkpoints/Tw_<Tw>/magnetization.csv
   ```

2. Yield one `(Tw, magnetization_df)` at a time.

3. Raise direct errors if a required checkpoint file is missing.

Also update save functions:

```text
save_final_simulation_outputs(...)
save_waiting_time_checkpoint(...)
```

Before saving spin arrays, cast to:

```python
np.int8
```

for:

```text
spin_release
spin_early_recovery
selected_spin_snapshots
```

This affects future simulation outputs. It does not change numerical meaning because
spin states are discrete `-1/+1`.

### File 2: `scripts/run_final_state_analysis.py`

Replace:

```python
simulation_data = load_final_simulation_outputs(paths)
analysis_result = run_final_state_analysis(simulation_data, params)
```

with a memory-aware flow:

```text
simulation_data = load_final_analysis_inputs(paths, params["feature_mode"])
recovery_dynamics = compute recovery dynamics from checkpoint magnetization files
analysis_result = run_final_state_analysis(simulation_data, params, recovery_dynamics)
```

Keep the script entry point simple. Add a few progress prints before expensive steps:

```text
[analysis] loading metadata and feature array
[analysis] running PCA
[analysis] running UMAP
[analysis] computing recovery dynamics from checkpoints
[analysis] saving outputs
```

These prints are scientifically useful because future failures will show which stage failed.

### File 3: `src/rccn_persistence/spin_analysis.py`

Adjust `run_final_state_analysis` so it can receive precomputed recovery dynamics:

```text
run_final_state_analysis(simulation_data, analysis_params, recovery_dynamics=None)
```

If `recovery_dynamics` is provided, use it directly.

If not provided, keep the old behavior:

```python
compute_recovery_dynamics_by_Tw(simulation_data["magnetization"], simulation_data["metadata"])
```

This preserves backward compatibility for smaller/debug runs.

Important targeted fix:

Current `build_spin_feature_matrix` does this:

```python
X_features = np.asarray(X_features, dtype=float)
```

This can force a huge full in-memory float64 copy.

For the first rescue pass, change it to use a smaller float type:

```python
X_features = np.asarray(X_features, dtype=np.float32)
```

This still creates a numeric matrix for PCA, but cuts the float matrix memory in half.

Avoid changing the feature representation in this first pass.

### File 4: optional later utility

Optional file:

```text
scripts/convert_final_spin_arrays_to_int8.py
```

Purpose:

Convert existing `.npy` files from the completed run to compact `int8` files without
rerunning simulation.

Recommended behavior:

1. Convert one file at a time.
2. Write to a temporary output path first:

   ```text
   selected_spin_snapshots.int8.tmp.npy
   ```

3. Verify shape and values.
4. Replace the original only after successful conversion.

This is optional for the first rescue pass because `mmap_mode="r"` may be enough.

## 7. Pseudocode

### `load_final_analysis_inputs(paths, feature_mode)`

Type: main analysis IO helper.

Input:

- `paths`
- `feature_mode`

Output:

- dictionary containing only the files needed by final analysis.

Pseudocode:

```text
simulation_dir = paths["final_simulation"]

read metadata.csv
read cycle_group_features.csv

if feature_mode == "selected_snapshots":
    load selected_spin_snapshots.npy with mmap_mode="r"
    read snapshot_metadata.csv

elif feature_mode == "release":
    load spin_release.npy with mmap_mode="r"

elif feature_mode == "early":
    load spin_early_recovery.npy with mmap_mode="r"

elif feature_mode == "release_plus_early":
    load spin_release.npy and spin_early_recovery.npy with mmap_mode="r"
    note: this mode may still need special handling because np.hstack can copy

else:
    raise ValueError

return simulation_data
```

### `compute_recovery_dynamics_from_checkpoints(paths, waiting_times, metadata)`

Type: memory-safe scientific summary.

Input:

- `paths`
- `waiting_times`
- `metadata`

Output:

- same table shape currently produced as `recovery_dynamics_by_Tw.csv`.

Pseudocode:

```text
tables = []

for Tw in waiting_times:
    checkpoint_path = final_simulation/checkpoints/Tw_<Tw>/magnetization.csv
    read checkpoint magnetization.csv
    select metadata rows for this Tw
    compute recovery dynamics for this Tw using existing compute function
    append small result table

return concat(tables)
```

Implementation note:

If the existing `compute_recovery_dynamics_by_Tw` already groups by `Tw`, use it on one
checkpoint at a time. Do not duplicate scientific formulas unless necessary.

### `save_spin_array_int8(path, array)`

Type: IO helper.

Input:

- destination path
- spin array

Output:

- `.npy` file containing `int8` spin states.

Pseudocode:

```text
if array contains values outside expected spin state range:
    raise ValueError

np.save(path, array.astype(np.int8, copy=False))
```

Keep the validation simple. Do not add a complex schema layer.

## 8. Execution order

Recommended order for implementation:

1. Add memory-aware analysis loader.
2. Update `run_final_state_analysis.py` to use the new loader.
3. Add checkpoint-based recovery dynamics computation.
4. Change spin array saving to `int8` for future runs/checkpoints.
5. Run only the analysis step on existing simulation outputs:

   ```powershell
   C:\work\env\python.exe scripts\run_final_state_analysis.py
   ```

6. If analysis succeeds, generate figures:

   ```powershell
   C:\work\env\python.exe scripts\make_final_project_figures.py
   ```

Do not rerun:

```powershell
scripts\run_final_rccn_simulation.py --preset final --workers 12
```

unless the existing simulation outputs are found to be corrupt or scientifically invalid.

## 9. Verification plan

Minimal verification:

1. Run import check:

   ```powershell
   C:\work\env\python.exe scripts\check_final_pipeline_imports.py
   ```

2. Run unit tests if available:

   ```powershell
   C:\work\env\python.exe -m pytest tests
   ```

3. Run final analysis only:

   ```powershell
   C:\work\env\python.exe scripts\run_final_state_analysis.py
   ```

4. Confirm these files exist:

   ```text
   output/result611/final_analysis/cell_state_table.csv
   output/result611/final_analysis/recovery_dynamics_by_Tw.csv
   output/result611/final_analysis/pca_scores.csv
   output/result611/final_analysis/umap_scores.csv
   ```

5. Run final figures:

   ```powershell
   C:\work\env\python.exe scripts\make_final_project_figures.py
   ```

6. Confirm:

   ```text
   output/result611/final_figures
   ```

## 10. Expected risk

The first pass may still fail at PCA because the feature matrix is large:

```text
10000 sampled states x 98304 spin features
```

Using `mmap_mode="r"` helps loading, and `float32` helps memory, but PCA still needs a
large numeric matrix.

If this still fails, the next scientifically explicit compromise should be:

```text
fixed-seed subsampling of spin features before PCA/UMAP
```

That second-stage change would alter the visualization feature representation, so it should
be documented as a methodological choice rather than hidden inside an IO refactor.


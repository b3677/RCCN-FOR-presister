# 2026-06-11 running record

This file records the final successful run, environment setup, known bugs, and cleanup
notes for the RCCN persistence final pipeline.

## 1. Final status

The final pipeline completed successfully after switching to a clean stable conda
environment and rerunning final analysis with full PCA.

Final simulation output:

```text
output/result611/final_simulation
```

Final analysis output:

```text
output/result611/final_analysis
```

Final figure output:

```text
output/result611/final_figures
```

Successful final analysis files:

```text
cell_state_table.csv
cluster_summary_by_Tw.csv
cycle_group_features.csv
cycle_pc1_moving_average.csv
pca_explained_variance.csv
pca_scores.csv
recovery_dynamics_by_Tw.csv
recovery_time_by_cluster.csv
tail_fraction_by_Tw.csv
umap_scores.csv
```

Successful final figures:

```text
figA_rccn_ageing_reproduction.png
figB_umap_by_Tw_recovery_time.png
figB_umap_recovery_time_exploration_6color.png
figC_cluster_occupancy_lag_by_cluster.png
figD_cycle_groups_along_PC1.png
figE_presister_like_PCA_UMAP.png
```

## 2. Final scientific run parameters

Saved in:

```text
output/result611/final_simulation/params.json
```

Key parameters:

```text
num_spins: 16384
n_runs: 2000
waiting_times: [0, 195, 488, 1346, 1500]
init_time: 2000
relax_time: 4050
max_cycle_length: 2500
early_recovery_delta: 20
baseline_window: 1000
gamma: 1.5
H_init: 0.0
H_stress: 0.8
H_relax: 0.0
random_seed: 1
selected_recovery_times: [0, 250, 500, 1000, 2000, 4000]
feature_mode: selected_snapshots
pca_components: 10
n_clusters: 3
umap_n_neighbors: 20
umap_min_dist: 0.2
sourcefig2_path: data/sourcefig2.xlsx
```

## 3. Environment that worked

Use this environment for analysis and plotting:

```text
C:\work\env_rccn_stable
```

Python:

```text
C:\work\env_rccn_stable\python.exe
```

Important package versions:

```text
python 3.11.15
numpy 1.26.4
pandas 2.3.3
scipy 1.11.4
matplotlib 3.10.9
scikit-learn 1.4.2
umap-learn 0.5.6
openpyxl 3.1.5
pytest 9.0.3
libblas 3.9.0 openblas
liblapack 3.9.0 openblas
libopenblas 0.3.25
```

The stable environment was created with conda-forge packages and OpenBLAS:

```powershell
conda create -p C:\work\env_rccn_stable -c conda-forge --strict-channel-priority python=3.11 "numpy=1.26.*" "scipy=1.11.*" "scikit-learn=1.4.*" pandas matplotlib umap-learn openpyxl pytest "libblas=*=*openblas" "liblapack=*=*openblas" -y
conda install -p C:\work\env_rccn_stable -c conda-forge "umap-learn=0.5.6" -y
```

Use these thread settings for stable fast PCA:

```powershell
$env:OPENBLAS_NUM_THREADS="4"
$env:OMP_NUM_THREADS="4"
$env:NUMEXPR_NUM_THREADS="4"
```

## 4. Commands that produced the final full-PCA outputs

Final analysis:

```powershell
cd C:\work\code\RCCN-FOR-presister-main\RCCN-FOR-presister-main

$env:OPENBLAS_NUM_THREADS="4"
$env:OMP_NUM_THREADS="4"
$env:NUMEXPR_NUM_THREADS="4"

C:\work\env_rccn_stable\python.exe scripts\run_final_state_analysis.py
```

Final figures:

```powershell
C:\work\env_rccn_stable\python.exe scripts\make_final_project_figures.py
```

Dependency check:

```powershell
C:\work\env_rccn_stable\python.exe scripts\check_final_pipeline_imports.py
```

Tests:

```powershell
C:\work\env_rccn_stable\python.exe -m pytest tests
```

Final test status:

```text
12 passed
```

## 5. Important bugs encountered

### Bug 1: old environment native crash during PCA

Old environment:

```text
C:\work\env
```

Symptoms:

- `python.exe` crashed without Python traceback.
- Windows Event Viewer showed `APPCRASH`.
- Faulting module: `KERNELBASE.dll`.
- Exception code: `0xc06d007f`.
- A small `IncrementalPCA.partial_fit` test could also crash.

Likely cause:

- Mixed or incompatible scientific Python stack.
- `scipy` was installed from `pypi`, while numpy / scikit-learn / BLAS came from
  conda-forge / MKL-linked packages.

Resolution:

- Stop using `C:\work\env` for final analysis.
- Use `C:\work\env_rccn_stable`.

### Bug 2: `umap-learn 0.5.12` incompatible with `scikit-learn 1.4.2`

Error:

```text
TypeError: check_array() got an unexpected keyword argument 'ensure_all_finite'
```

Cause:

- `umap-learn 0.5.12` expected a newer scikit-learn API.

Resolution:

```powershell
conda install -p C:\work\env_rccn_stable -c conda-forge "umap-learn=0.5.6" -y
```

### Bug 3: large `.npy` arrays were initially too large

Original spin arrays were stored as large numeric arrays even though spin values are only
`-1/+1`.

Resolution:

- Save final spin arrays as `int8`.
- Convert existing arrays to `int8`.

Current official `.npy` files are compact `int8`.

## 6. Code changes made during rescue

### Memory-safe final analysis loading

`scripts/run_final_state_analysis.py` now uses:

```text
load_final_analysis_inputs
compute_recovery_dynamics_from_checkpoints
```

This avoids loading unnecessary large arrays and avoids reading the merged
`magnetization.csv` for recovery dynamics.

### Compact spin-array saving

Final simulation and checkpoint spin arrays are saved as `int8`:

```text
spin_release.npy
spin_early_recovery.npy
selected_spin_snapshots.npy
```

This does not change spin-state meaning because values are `-1/+1`.

### Full PCA restored

The final analysis now uses full sklearn PCA by default:

```text
run_pca(..., method="full")
```

`IncrementalPCA` remains available only as an explicit fallback:

```text
pca_method: incremental
```

The final official outputs were regenerated after full PCA was restored.

## 7. Diagnostic and intermediate outputs

These are not final scientific outputs:

```text
output/result611/pca_diagnostics
output/result611/final_figures_pcatest
```

They can be deleted if disk clarity matters.

These backup files can be deleted after confirming final outputs are accepted:

```text
output/result611/final_simulation/**/*.npy.int64.bak
```

They are old pre-conversion backups. The current official `.npy` files are already `int8`.

Do not delete:

```text
output/result611/final_simulation
output/result611/final_analysis
output/result611/final_figures
```

## 8. Cleanup recommendation

Cleanup completed after final outputs were confirmed:

- Deleted diagnostic output directory:

  ```text
  output/result611/pca_diagnostics
  ```

- Deleted diagnostic output directory:

  ```text
  output/result611/final_figures_pcatest
  ```

- Checked for old backup files:

  ```text
  output/result611/final_simulation/**/*.npy.int64.bak
  ```

  No matching backup files remained at cleanup time.

- Added top-level maintenance docstrings to:

  ```text
  scripts/convert_final_spin_arrays_to_int8.py
  scripts/run_final_pca_only.py
  ```

Post-cleanup validation:

```text
pytest: 12 passed
```

Remaining recommendation:

1. Keep the code unchanged for the final report.
2. Keep `scripts/convert_final_spin_arrays_to_int8.py` and `scripts/run_final_pca_only.py`
   as maintenance/diagnostic utilities unless the user wants a polished release.
3. Do not use `C:\work\env` for final analysis.
4. Use `C:\work\env_rccn_stable` for analysis and plotting.

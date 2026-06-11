# Final code cleanup review and refactor plan

Date: 2026-06-11

This document follows the Scientific Code Reviewer / Scientific Code Refactorer
workflow. It is a plan only. It does not authorize code deletion or behavior changes
until the user confirms.

## 1. Global map

### Scientific task

The current final pipeline simulates RCCN spin-glass recovery dynamics, analyzes
high-dimensional spin-state features with PCA / UMAP / clustering, and generates final
project figures.

### Main inputs

- Model parameters from `src/rccn_persistence/config.py`.
- Simulation outputs in `output/result611/final_simulation`.
- Source tail-fraction reference table: `data/sourcefig2.xlsx`.

### Main outputs

- Final analysis tables:

  ```text
  output/result611/final_analysis
  ```

- Final figures:

  ```text
  output/result611/final_figures
  ```

### Current final workflow

```text
scripts/run_final_rccn_simulation.py
  -> src/rccn_persistence/simulation.py
  -> src/rccn_persistence/io_utils.py
  -> output/result611/final_simulation

scripts/run_final_state_analysis.py
  -> load final simulation inputs
  -> compute recovery dynamics from checkpoints
  -> run full PCA on selected spin snapshots
  -> run UMAP
  -> run clustering
  -> save final analysis tables

scripts/make_final_project_figures.py
  -> read final analysis tables
  -> save final figure PNGs
```

## 2. Current review findings

### Finding A: Core final pipeline is acceptable

The final pipeline now uses full PCA again by default. This returns the scientific
analysis path to the intended full-PCA interpretation.

Relevant current behavior:

- `run_pca(..., method="full")` is the default.
- `IncrementalPCA` remains only as an explicit fallback via `pca_method="incremental"`.
- The final analysis and figures have already been regenerated with full PCA.

This is scientifically cleaner than leaving IncrementalPCA as the default.

### Finding B: Some diagnostic code remains

The following scripts were created during rescue/debugging:

```text
scripts/convert_final_spin_arrays_to_int8.py
scripts/run_final_pca_only.py
```

They are not part of the everyday final pipeline, but they are useful reproducibility
utilities:

- `convert_final_spin_arrays_to_int8.py` documents and repeats the safe conversion of
  spin arrays from large floating/int64 files into compact `int8` files.
- `run_final_pca_only.py` isolates PCA diagnostics from the full analysis pipeline.

Recommendation:

- Keep both scripts for now, but clearly mark them as maintenance/diagnostic scripts.
- Do not delete them immediately, because they explain the environment rescue path and
  make future PCA checks reproducible.

### Finding C: Some diagnostic output directories can be deleted or archived

These are not needed for final scientific results:

```text
output/result611/pca_diagnostics
output/result611/final_figures_pcatest
```

Recommendation:

- They can be deleted after the user confirms that full-PCA final outputs are accepted.
- They should not be confused with final outputs.

Do not delete:

```text
output/result611/final_analysis
output/result611/final_figures
output/result611/final_simulation
```

### Finding D: Old first-version spin clustering code still exists

At the top of `src/rccn_persistence/spin_analysis.py`, the first-version clustering
helpers still exist:

```text
center_spin_matrix
run_pca_on_spins
cluster_pca_scores
summarize_cluster_occupancy
summarize_recovery_by_cluster
run_spin_clustering_analysis
```

These are used by:

```text
scripts/run_spin_clustering.py
```

Therefore they are not dead code. They support the earlier non-final pipeline.

Recommendation:

- Do not delete them unless the old first-version pipeline is intentionally retired.
- If the final project is now the only workflow that matters, move first-version analysis
  into a clearly named legacy module later.

## 3. Does the code need immediate refactoring?

No urgent core-code refactor is needed.

The current final pipeline is readable enough:

- entry scripts remain thin;
- simulation, IO, analysis, and plotting are separated;
- final outputs are stable;
- failures are mostly direct;
- scientific parameters are explicit in `config.py` and `params.json`.

However, there is a small cleanup opportunity around diagnostic scripts and output
directories. This should be treated as housekeeping, not scientific refactoring.

## 4. Proposed cleanup plan

Only do this after user confirmation.

### Step 1: Add explicit comments/docstrings for diagnostic scripts

Files:

```text
scripts/convert_final_spin_arrays_to_int8.py
scripts/run_final_pca_only.py
```

Change:

- Add a short top-level docstring explaining that these are maintenance/diagnostic scripts.
- State that they are not part of the normal final pipeline.

Scientific effect:

- None.

### Step 2: Optionally archive or delete diagnostic output directories

Candidate directories:

```text
output/result611/pca_diagnostics
output/result611/final_figures_pcatest
```

Recommended default:

- Delete only if disk space or clarity matters.
- Otherwise leave them and document that final outputs live elsewhere.

Scientific effect:

- None if final outputs are preserved.

### Step 3: Optionally move first-version spin clustering into a legacy module

Candidate source:

```text
src/rccn_persistence/spin_analysis.py
```

Current issue:

- The file contains both first-version spin clustering and final-project state analysis.
- This is understandable historically, but a little cognitively expensive.

Possible future target:

```text
src/rccn_persistence/spin_clustering_legacy.py
src/rccn_persistence/spin_analysis.py
```

Keep:

```text
scripts/run_spin_clustering.py
```

but update imports.

Scientific effect:

- None if functions are moved unchanged.
- Requires tests before and after.

Recommendation:

- Do not do this today unless the user wants a cleaner codebase for long-term reuse.
- It is easy to over-clean and accidentally distract from the final project.

## 5. Pseudocode for safe cleanup

### Function: mark_diagnostic_scripts

Role:

Make transition scripts understandable without changing behavior.

Pseudocode:

```text
for each diagnostic script:
    add top-level docstring
    explain when to use it
    explain normal pipeline does not call it
run py_compile
run pytest
```

### Function: delete_confirmed_diagnostic_outputs

Role:

Remove only output directories that are not final results.

Pseudocode:

```text
confirm final_analysis exists
confirm final_figures exists
confirm user wants deletion
delete output/result611/pca_diagnostics
delete output/result611/final_figures_pcatest
do not delete final_simulation
do not delete final_analysis
do not delete final_figures
```

### Function: optionally_move_legacy_spin_clustering

Role:

Separate old first-version clustering from final-project analysis.

Pseudocode:

```text
create spin_clustering_legacy.py
move first-version helper functions unchanged
update run_spin_clustering.py imports
leave final-project functions in spin_analysis.py
run tests
run old debug clustering command if needed
```

## 6. Recommended decision

Recommended now:

1. Keep code as-is for the final report.
2. Delete or ignore diagnostic output directories only after user confirmation.
3. Keep diagnostic scripts because they document important rescue operations.
4. Do not move legacy functions today unless the user wants long-term maintenance cleanup.


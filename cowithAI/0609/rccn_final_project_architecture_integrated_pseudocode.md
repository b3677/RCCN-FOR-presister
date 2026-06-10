# RCCN final project: architecture-integrated pseudocode

## 0. Purpose

This document turns `rccn_final_project_plot_requirements.md` into an implementation-oriented pseudocode plan that fits the current repository.

The goal is not to write full Python code yet. The goal is to make the scientific workflow clear enough that the next coding step can be small, readable, and maintainable.

The design follows the Scientific Code Scholar rule:

1. start from the scientific question;
2. keep the mathematical and biological meaning visible;
3. write pseudocode before code;
4. avoid over-engineered architecture;
5. let real data/path/column errors fail clearly near their source.

---

## 1. Current Scientific Goal

The project currently has a working first-version RCCN simulation pipeline:

```text
RCCN network construction
    -> spin dynamics under initialization / stress / recovery
    -> magnetization and recovery time
    -> release and early-recovery spin snapshots
    -> PCA and simple k-means clustering
    -> first-pass project figures
```

The final-project plotting requirements extend this into a more complete single-cell state analysis:

```text
RCCN simulation at specific Tw values
    -> recovery dynamics validation
    -> sampled cell-state feature table at recovery times 0, 20, 120 min
    -> PCA / UMAP low-dimensional state space
    -> tail-fraction-derived presister-like labels
    -> cluster occupancy and lag-time summaries
    -> cycle-group summary interpretation along PC1
    -> final report figures A-E
```

The central scientific question is:

```text
Can RCCN-generated spin states reproduce waiting-time-dependent recovery ageing,
and do slow-recovering simulated cells occupy a distinguishable state-space region
similar to experimentally observed persister-like cell states?
```

Implementation priority requested for the next coding stage:

```text
First complete Fig. A, Fig. C, Fig. E, and Fig. B as fully as the data allow.
If a requirement needs extra saved data, add that data product instead of simplifying the figure.
After A/C/E/B are running, implement Fig. D using the per-cell cycle group summary strategy.
```

---

## 2. Existing Architecture

Current package layout:

```text
src/rccn_persistence/
    config.py
    network.py
    dynamics.py
    observables.py
    simulation.py
    io_utils.py
    spin_analysis.py
    plotting.py

scripts/
    run_rccn_simulation.py
    run_spin_clustering.py
    make_project_figures.py
```

Current outputs:

```text
output/rccn_simulation/
    params.json
    metadata.csv
    magnetization.csv
    spin_release.npy
    spin_early_recovery.npy

output/spin_clustering/
    pca_scores.csv
    pca_explained_variance.csv
    cluster_labels.csv
    cluster_occupancy_by_Tw.csv
    recovery_time_by_cluster.csv

output/figures/
    fig1_recovery_survival_by_Tw.png
    fig2_spin_pca_by_Tw.png
    fig3_spin_pca_by_cluster.png
    fig4_spin_pca_by_recovery_time.png
    fig5_cluster_occupancy_by_Tw.png
    fig6_spin_pca_by_regrowth_vs_persister.png
    fig7_regrowth_vs_persister_fraction_by_Tw.png
```

The existing code already has a useful separation:

| File | Keep? | Reason |
|---|---|---|
| `config.py` | keep and extend | Central place for default/final plotting parameters |
| `network.py` | keep | Scientific core aligned with MATLAB RCCN construction |
| `dynamics.py` | keep, lightly extend | Spin update and protocol are core model logic |
| `observables.py` | keep and extend | Right place for recovery curves, tail labels, summary tables |
| `simulation.py` | keep, lightly extend | Batch simulation already readable |
| `io_utils.py` | keep and extend | Good place for stable read/write of analysis products |
| `spin_analysis.py` | partially rewrite | Current PCA/k-means is first-pass; final needs feature tables, PCA, UMAP, clustering, PC1 summaries |
| `plotting.py` | mostly rewrite or split | Current functions are quick-look plots; final figures A-E need clearer dedicated functions |
| `scripts/*.py` | keep script-entry pattern | Useful execution layer; scripts can be updated or new final scripts can be added |

---

## 3. Main Gaps Between Current Code and Final Requirements

### 3.1 Waiting Times

Current defaults:

```text
[20, 40, 80, 160, 320, 640, 1280, 3000]
```

Final requirements:

```text
[0, 195, 488, 1346, 1500]
```

Pseudocode decision:

```text
Add final-project parameters without deleting the existing debug/default presets.
Use explicit command-line overrides or a new make_final_project_params().
```

### 3.2 Cell-Level Analysis Table

Current output separates:

```text
metadata.csv
pca_scores.csv
cluster_labels.csv
spin_release.npy
spin_early_recovery.npy
```

Final requirements need one analysis table with stable row identity:

```text
simulation_id
Tw
state_recovery_time
recovery_time
lag_time
recovered_label
cluster_id
presister_like
PC1
PC2
UMAP1
UMAP2
```

Pseudocode decision:

```text
Create a new cell_state_table.csv after dimensionality reduction and labeling.
For Fig. B, this table should have one row per simulation_id / Tw / sampled state_recovery_time.
For Fig. C and Fig. E, use the biologically chosen state snapshot, usually release or release + early-recovery features,
or aggregate/choose one state row per simulation_id explicitly.
Do not hide high-dimensional spin vectors inside CSV.
Keep spin feature matrices as .npy files and link rows by run_id / simulation_id.
```

### 3.3 Tail-Fraction Labels

Current code defines persister-like cells mainly as:

```text
unrecovered cells, or cells beyond a manually chosen recovery threshold
```

Final requirement:

```text
Within each Tw group, classify the slowest-recovering TailFraction fraction
as presister-like.
```

Pseudocode decision:

```text
Add tail-fraction loading and extrapolation from data/sourcefig2.xlsx.
Use the tail fraction within each Tw group, not globally.
```

### 3.4 UMAP

Current code has only PCA by NumPy SVD.

Final figures B and E require UMAP.

Pseudocode decision:

```text
Add UMAP as an optional dependency-backed analysis step.
If umap-learn is unavailable, the code should raise a clear ImportError
when UMAP is requested.
Do not silently replace UMAP with PCA.
```

### 3.5 Clustering

Current clustering is a small hand-written k-means on PCA scores.

For the final project, that code can be replaced if needed.

Pseudocode decision:

```text
Prefer sklearn PCA / StandardScaler / KMeans if available.
This is acceptable because clustering is not the RCCN scientific core.
If dependency management is a concern, keep the current SVD PCA but rewrite
the analysis flow around stable tables.
```

### 3.6 Cycle-Level PC1 Interpretation

Current simulation does not save cycle-level features for every cell.

But `network.py` creates a new RCCN network for each simulated cell, so cycle identities are not shared across all cells.

Important scientific implication:

```text
Fig. D is not a simple plotting add-on.
If each cell has a different random network, cycle_id is not comparable across cells.
```

Pseudocode decision:

```text
Use the per-cell cycle summary strategy for Fig. D.
Keep one random RCCN network per simulated cell.
Do not compare concrete cycle_id values across cells.
Instead, for each cell, compute:
    - short cycles mean magnetization
    - medium cycles mean magnetization
    - long cycles mean magnetization
Then plot moving averages of these three summaries along PC1.
```

This is a deliberate simplification of the pathway-like Fig. 3c logic, but it preserves the scientifically meaningful comparison that remains valid when each cell has its own random RCCN network.

---

## 4. Scientific Assumptions to Preserve

The following should not change while implementing final figures:

1. RCCN cycle length sampling follows the MATLAB `initJij.m` logic.
2. Within-cycle shift edges follow the current `build_shift_edges()` behavior.
3. Spin update is synchronous.
4. `local_field == 0` keeps the previous spin.
5. Global magnetization uses cycle-averaged magnetization.
6. Recovery time is the first recovery-step index where magnetization is strictly below baseline.
7. One simulation run is treated as one model single cell.
8. One simulation step is displayed as approximately one minute.

The most important possible scientific change is the feature definition for PCA/UMAP:

```text
release snapshot only
early recovery snapshot only
release + early recovery concatenated
cycle-averaged features
```

Recommended first final-project choice:

```text
Use release + early recovery spin snapshots as the primary state feature matrix.
This captures both stress-release state and early recovery direction.
Also allow release-only as a simple sensitivity check.
```

---

## 5. Target Output Products

Final analysis should save these tables:

```text
output/final_analysis/
    tail_fraction_by_Tw.csv
    recovery_dynamics_by_Tw.csv
    cell_state_table.csv
    pca_scores.csv
    umap_scores.csv
    cluster_summary_by_Tw.csv
    recovery_time_by_cluster.csv
    cycle_group_features.csv
    cycle_pc1_moving_average.csv      # Fig. D group-summary version
```

Final figures should save:

```text
output/final_figures/
    figA_rccn_ageing_reproduction.png
    figB_umap_by_Tw_recovery_time.png
    figC_cluster_occupancy_lag_by_cluster.png
    figD_cycle_groups_along_PC1.png
    figE_presister_like_PCA_UMAP.png
```

The existing `output/spin_clustering/` and `output/figures/` can remain as first-pass outputs.
The final pipeline should write to separate directories to avoid confusing old exploratory files with final products.

---

## 6. Recommended File-Level Implementation Plan

### 6.1 `config.py`

Add:

```text
make_final_project_params()
```

Purpose:

```text
Hold final Tw values, n_runs, selected recovery times, PCA/UMAP/clustering settings,
and paths to sourcefig2.xlsx.
```

### 6.2 `simulation.py`

Mostly keep current functions.

Potential extension:

```text
Save feature snapshots at selected recovery times:
recovery_time = 0, 20, 120 min
```

Required implementation for Fig. B without simplification:

```text
Extend dynamics.py / run_one_protocol() so the simulation saves snapshots at:
    - release + 0
    - release + 20
    - release + 120
Save a snapshot_metadata.csv table that links each snapshot row to:
    - run_id
    - Tw
    - state_recovery_time
The old spin_release.npy and spin_early_recovery.npy can remain for compatibility,
but final Fig. B should use the selected-snapshot matrix.
For Fig. D, compute short/medium/long cycle-group magnetization while each cell's network metadata is still available.
```

### 6.3 `observables.py`

Add:

```text
compute_recovery_dynamics_by_Tw()
load_tail_fraction_table()
extrapolate_tail_fraction()
assign_presister_like_by_tail_fraction()
summarize_cluster_by_Tw()
```

These are scientific table functions, not plotting functions.

### 6.4 `spin_analysis.py`

Rewrite around final cell-state workflow:

```text
build_spin_feature_matrix()
run_pca()
run_umap()
run_clustering()
build_cell_state_table()
compute_cycle_group_features()
compute_cycle_pc1_moving_average()
run_final_state_analysis()
```

The old `cluster_pca_scores()` can be deleted or kept only as fallback.
If using sklearn, prefer sklearn's `KMeans` because it is tested and standard.

### 6.5 `plotting.py`

The current quick-look plot functions can stay, but final figures should use dedicated names:

```text
plot_figA_recovery_dynamics()
plot_figB_umap_by_Tw_recovery_time()
plot_figC_cluster_occupancy_and_lag()
plot_figD_cycle_groups_along_PC1()
plot_figE_presister_like_pca_umap()
```

Each plotting function should read already-computed table columns.
Plotting functions should not compute PCA, UMAP, clusters, or tail labels.

### 6.6 `io_utils.py`

Add:

```text
make_final_output_paths()
save_final_analysis_outputs()
load_final_analysis_outputs()
```

Keep this simple: explicit filenames, no automatic path guessing.

### 6.7 New Scripts

Recommended new script names:

```text
scripts/run_final_rccn_simulation.py
scripts/run_final_state_analysis.py
scripts/make_final_project_figures.py
```

Reason:

```text
Keep old first-pass scripts runnable.
Use final scripts for final-report products.
```

---

## 7. Pipeline Pseudocode

### 7.1 Final Simulation Pipeline

```text
function run_final_rccn_simulation():
    1. project_root = repository root
    2. params = make_final_project_params()
    3. allow command-line overrides for:
        - n_runs
        - num_spins
        - waiting_times
        - seed
        - selected snapshot recovery times
    4. create output/final_simulation or reuse output/rccn_simulation if chosen explicitly
    5. run_batch(params)
    6. save:
        - params.json
        - metadata.csv
        - magnetization.csv
        - spin_release.npy
        - selected_spin_snapshots.npy
        - snapshot_metadata.csv
        - cycle_group_features.csv
    7. print output directory
```

Code type:

```text
主干逻辑 / script entry
```

Complexity reminder:

```text
Keep this script thin. It should only parse parameters and call simulation/io functions.
```

### 7.2 Final State Analysis Pipeline

```text
function run_final_state_analysis():
    1. load simulation outputs
    2. load or compute tail_fraction_by_Tw
    3. build spin_state_feature_matrix from selected_spin_snapshots.npy
    4. run PCA on feature matrix
    5. run UMAP on feature matrix or PCA scores
    6. run clustering on PCA scores or feature matrix
    7. assign presister_like labels within each Tw using tail fractions
    8. build cell_state_table with one row per run_id / state_recovery_time
    9. compute recovery_dynamics_by_Tw
    10. compute cluster_summary_by_Tw
    11. compute cycle_pc1_moving_average from cycle_group_features and PC1
    12. save all analysis tables
```

Code type:

```text
主干逻辑 / script entry
```

Complexity reminder:

```text
This script can call many functions, but should not contain analysis details inline.
```

### 7.3 Final Figure Pipeline

```text
function make_final_project_figures():
    1. load final analysis tables
    2. create output/final_figures
    3. plot Fig. A from recovery_dynamics_by_Tw
    4. plot Fig. C from cluster_summary_by_Tw and cell_state_table
    5. plot Fig. E from cell_state_table
    6. plot Fig. B from cell_state_table and tail_fraction_by_Tw
    7. plot Fig. D from cycle_pc1_moving_average and cell_state_table
    8. save PNG and optionally SVG/PDF
```

Code type:

```text
绘图主干逻辑 / script entry
```

Complexity reminder:

```text
Do not recompute PCA/UMAP/clustering here.
```

---

## 8. Function-Level Pseudocode

## File: `src/rccn_persistence/config.py`

### `make_final_project_params()`

作用:

```text
Return final-project settings for simulation and analysis.
```

输入:

```text
None
```

输出:

```text
params dictionary
```

伪代码:

```text
function make_final_project_params():
    1. start from make_default_params()
    2. set waiting_times = [0, 195, 488, 1346, 1500]
    3. set n_runs = 900 for final run
    4. set selected_recovery_times = [0, 20, 120]
    5. set early_recovery_delta = 20 or keep as separate snapshot rule
    6. set pca_components = 10
    7. set n_clusters = 3 or 4 as first explicit choice
    8. set sourcefig2_path = data/sourcefig2.xlsx
    9. set state_recovery_time_for_cluster_summary = 0
    10. set state_recovery_time_for_figE = 0
    11. set state_recovery_time_for_figD = 0
    12. set figD_window_size
    13. set random_seed
    14. return params
```

代码类型标注:

```text
主干配置
```

复杂度提醒:

```text
Keep as a flat dictionary. Do not introduce a config class.
```

---

## File: `src/rccn_persistence/dynamics.py`

### `run_one_protocol(network, params, Tw, rng)`

作用:

```text
Run one RCCN protocol and save exact selected recovery snapshots for Fig. B.
```

输入:

```text
network
params with selected_recovery_times = [0, 20, 120]
Tw
rng
```

输出:

```text
protocol_result with magnetization, selected_snapshots, zero_field_count, and compatibility snapshots
```

伪代码:

```text
function run_one_protocol(network, params, Tw, rng):
    1. initialize spins
    2. compute release_time = init_time + Tw
    3. compute selected absolute snapshot times:
        release_time + 0
        release_time + 20
        release_time + 120
    4. run the existing time loop
    5. at each time:
        5.1 record magnetization
        5.2 if time is one of the selected snapshot times:
            save spins.copy() into selected_snapshots keyed by state_recovery_time
        5.3 keep old release_snapshot and early_recovery_snapshot outputs for compatibility
        5.4 update spins using the existing synchronous update rule
    6. after the loop, require all selected snapshots to be present
    7. return protocol_result
```

代码类型标注:

```text
主干模拟逻辑
```

复杂度提醒:

```text
This is a small extension of the current function.
Do not change the spin update rule or recovery-time definition.
```

---

## File: `src/rccn_persistence/simulation.py`

### `run_one_cell(params, Tw, run_id, rng)`

作用:

```text
Run one simulated cell and package metadata, selected snapshots, and Fig. D cycle group summaries.
```

输入:

```text
params
Tw
run_id
rng
```

输出:

```text
one-cell result dictionary
```

伪代码:

```text
function run_one_cell(params, Tw, run_id, rng):
    1. build one RCCN network for this cell
    2. call run_one_protocol() with selected_recovery_times
    3. compute recovery_time from magnetization as before
    4. build one metadata row for this simulated cell
    5. build snapshot_metadata rows:
        for each selected state_recovery_time:
            - run_id
            - Tw
            - state_recovery_time
            - absolute_snapshot_time
    6. stack selected snapshots in the same order as snapshot_metadata
    7. for each selected snapshot:
        compute short/medium/long cycle group features using this cell's cycle_starts and cycle_lengths
    8. return:
        - metadata row
        - magnetization table
        - selected snapshot matrix
        - snapshot_metadata rows
        - cycle_group_features rows
        - old release/early snapshots for compatibility
```

代码类型标注:

```text
主干模拟包装
```

复杂度提醒:

```text
This is where Fig. D data should be computed, because network cycle metadata is still available here.
Do not try to reconstruct cycle groups later from saved spin matrices alone.
```

### `run_batch(params)`

作用:

```text
Run all Tw values and save row-aligned selected snapshots for final analysis.
```

输入:

```text
params
```

输出:

```text
batch_result with metadata, magnetization, selected_spin_snapshots, snapshot_metadata, cycle_group_features
```

伪代码:

```text
function run_batch(params):
    1. initialize rng
    2. for each Tw:
        2.1 run n_runs cells
        2.2 append metadata rows
        2.3 append magnetization rows
        2.4 append selected snapshot rows and snapshot_metadata rows
        2.5 append cycle_group_features rows
    3. concatenate metadata
    4. concatenate magnetization
    5. stack selected_spin_snapshots
    6. concatenate snapshot_metadata
    7. concatenate cycle_group_features
    8. return batch_result
```

代码类型标注:

```text
主干批处理
```

复杂度提醒:

```text
The selected snapshot matrix row order must exactly match snapshot_metadata.
```

---

## File: `src/rccn_persistence/observables.py`

### `compute_recovery_dynamics_by_Tw(magnetization, metadata)`

作用:

```text
Compute Fig. A table: mean recovery observable over runs at each Tw and recovery time.
```

输入:

```text
magnetization table with run_id, Tw, time, magnetization
metadata table with Tw and snapshot/release time information
```

输出:

```text
recovery_dynamics_by_Tw DataFrame
```

伪代码:

```text
function compute_recovery_dynamics_by_Tw(magnetization, metadata):
    1. merge magnetization with each run's release time from metadata
    2. compute recovery_time = absolute time - snapshot_time
    3. keep rows with recovery_time >= 0
    4. group by Tw and recovery_time
    5. compute:
        - mean_recovery_observable = mean magnetization
        - std_recovery_observable
        - sem_recovery_observable
        - n_simulations
    6. return table ordered by Tw and recovery_time
```

代码类型标注:

```text
主干科学计算
```

复杂度提醒:

```text
This should stay as one clear groupby function.
```

### `load_tail_fraction_table(sourcefig2_path, target_waiting_times)`

作用:

```text
Load Kaplan Fig. 2c-derived tail fractions and add extrapolated Tw values if needed.
```

输入:

```text
sourcefig2_path
target_waiting_times
```

输出:

```text
tail_fraction_by_Tw DataFrame with Tw, TailFraction, TailFractionSTD, TailFraction_source
```

伪代码:

```text
function load_tail_fraction_table(sourcefig2_path, target_waiting_times):
    1. read Excel file with pandas.read_excel
    2. require columns:
        - Tw_minutes
        - TailFraction
        - TailFractionSTD
    3. rename Tw_minutes to Tw
    4. for each target Tw:
        4.1 if Tw exists in source table:
            use direct TailFraction and TailFractionSTD
            set TailFraction_source = sourcefig2_direct
        4.2 if Tw is missing:
            call extrapolate_tail_fraction()
            set TailFraction_source = sourcefig2_extrapolated
    5. return rows for target_waiting_times only
```

代码类型标注:

```text
辅助科学数据加载
```

复杂度提醒:

```text
Fail clearly if the expected columns are missing.
```

### `extrapolate_tail_fraction(source_table, target_Tw)`

作用:

```text
Estimate TailFraction for Tw values not directly present in sourcefig2.xlsx.
```

输入:

```text
source table
target_Tw
```

输出:

```text
TailFraction, TailFractionSTD
```

伪代码:

```text
function extrapolate_tail_fraction(source_table, target_Tw):
    1. sort source table by Tw
    2. choose a simple explicit model:
        option A: linear interpolation/extrapolation on TailFraction vs Tw
        option B: linear interpolation/extrapolation on logit(TailFraction) vs Tw
    3. for first implementation, use option A unless TailFraction is near 0 or 1
    4. fit using available source points
    5. predict target_Tw
    6. clip result to [0, 1]
    7. estimate TailFractionSTD as nearest-neighbor STD or linearly extrapolated STD
    8. return values
```

代码类型标注:

```text
辅助科学计算
```

复杂度提醒:

```text
State the extrapolation choice in the figure caption or output table.
Do not overfit a complex model to a few source points.
```

### `assign_presister_like_by_tail_fraction(metadata, tail_fraction_table)`

作用:

```text
Within each Tw group, label the slowest-recovering TailFraction fraction as presister-like.
```

输入:

```text
metadata with run_id, Tw, recovery_time, recovered
tail_fraction_table
```

输出:

```text
metadata with presister_like boolean and state_label
```

伪代码:

```text
function assign_presister_like_by_tail_fraction(metadata, tail_fraction_table):
    1. copy metadata
    2. initialize presister_like = False
    3. for each Tw group:
        3.1 read TailFraction for this Tw
        3.2 compute n_presister = ceil(group_size * TailFraction)
        3.3 rank cells by recovery_time from slowest to fastest
            - unrecovered / NaN recovery_time should be treated as slowest
        3.4 label top n_presister cells as presister_like = True
    4. set state_label = "presister-like" or "normal"
    5. return labeled metadata
```

代码类型标注:

```text
主干科学标签计算
```

复杂度提醒:

```text
This is scientifically important. Keep the ranking rule explicit and test it.
```

### `summarize_cluster_by_Tw(cell_state_table, state_recovery_time_for_summary)`

作用:

```text
Compute cluster occupancy and recovery summaries for Fig. C.
```

输入:

```text
cell_state_table with Tw, state_recovery_time, cluster_id, recovery_time, presister_like
state_recovery_time_for_summary, usually 0 min
```

输出:

```text
cluster_summary_by_Tw
```

伪代码:

```text
function summarize_cluster_by_Tw(cell_state_table, state_recovery_time_for_summary):
    1. filter cell_state_table to one state_recovery_time, usually 0 min
    2. group by Tw and cluster_id
    3. compute n_cells
    4. compute cluster_fraction within each Tw
    5. compute mean_lag_time = mean recovery_time
    6. compute median_lag_time
    7. compute presister_like_fraction
    8. optionally compute mean_PC1 and mean_PC2
    9. return ordered summary table
```

代码类型标注:

```text
主干科学 summary
```

复杂度提醒:

```text
Keep this table as the only source for Fig. C left.
Do not count the same simulated cell multiple times across 0/20/120 snapshots for Fig. C.
```

---

## File: `src/rccn_persistence/spin_analysis.py`

### `build_spin_feature_matrix(simulation_data, feature_mode)`

作用:

```text
Build the matrix used for PCA, UMAP, and clustering.
```

输入:

```text
simulation_data dictionary
feature_mode: "selected_snapshots", "release", "early", "release_plus_early"
```

输出:

```text
X_features
feature_metadata
```

伪代码:

```text
function build_spin_feature_matrix(simulation_data, feature_mode):
    1. read selected_spin_snapshots matrix and snapshot_metadata if feature_mode == "selected_snapshots"
    2. read spin_release matrix and spin_early_recovery matrix only for compatibility/sensitivity checks
    3. if feature_mode == "selected_snapshots":
        X = selected_spin_snapshots
        feature_metadata = snapshot_metadata
    4. if feature_mode == "release":
        X = spin_release
        feature_metadata = metadata copied with state_recovery_time = 0
    5. if feature_mode == "early":
        X = spin_early_recovery
        feature_metadata = metadata copied with state_recovery_time = early_recovery_delta
    6. if feature_mode == "release_plus_early":
        X = concatenate release and early matrices column-wise
        feature_metadata = metadata copied with state_recovery_time = "release_plus_early"
    7. convert X to float
    8. check X row count equals feature_metadata row count
    9. return X, feature_metadata
```

代码类型标注:

```text
主干分析准备
```

复杂度提醒:

```text
Do not add many feature modes initially.
Use selected_snapshots as the primary mode for Fig. B.
Use release_plus_early only as a sensitivity mode for Fig. C/E if needed.
```

### `run_pca(X_features, n_components, random_seed)`

作用:

```text
Compute PCA coordinates for spin-state features.
```

输入:

```text
X_features
n_components
random_seed
```

输出:

```text
pca_scores table
explained_variance table
optional fitted PCA object
```

伪代码:

```text
function run_pca(X_features, n_components, random_seed):
    1. center or standardize X_features
    2. choose max_components <= min(n_samples, n_features)
    3. fit PCA
    4. transform X_features to PC scores
    5. create columns PC1, PC2, ...
    6. create explained_variance_ratio table
    7. return scores and explained variance
```

代码类型标注:

```text
主干降维
```

复杂度提醒:

```text
If sklearn is used, this function becomes short.
If NumPy SVD is kept, reuse the existing logic but make the output table stable.
```

### `run_umap(X_for_embedding, random_seed)`

作用:

```text
Compute UMAP coordinates for Fig. B and Fig. E.
```

输入:

```text
feature matrix or PCA score matrix
random_seed
```

输出:

```text
umap_scores table with UMAP1, UMAP2
```

伪代码:

```text
function run_umap(X_for_embedding, random_seed):
    1. import umap
    2. if import fails:
        raise ImportError explaining that umap-learn is needed
    3. initialize UMAP with:
        - n_components = 2
        - random_state = random_seed
        - reasonable n_neighbors and min_dist
    4. fit_transform X_for_embedding
    5. return table with UMAP1 and UMAP2
```

代码类型标注:

```text
主干降维
```

复杂度提醒:

```text
Do not silently fall back to PCA because Fig. B/E explicitly request UMAP.
```

### `run_clustering(X_for_clustering, n_clusters, random_seed)`

作用:

```text
Assign unsupervised spin-state clusters.
```

输入:

```text
PCA score matrix or feature matrix
n_clusters
random_seed
```

输出:

```text
cluster label array/table
```

伪代码:

```text
function run_clustering(X_for_clustering, n_clusters, random_seed):
    1. choose clustering input, preferably first several PCs
    2. fit KMeans with n_clusters
    3. return labels as cluster_id
```

代码类型标注:

```text
主干聚类
```

复杂度提醒:

```text
Old manual k-means can be abandoned if sklearn is used.
Do not implement cluster-number search in the first final version.
```

### `build_cell_state_table(feature_metadata, pca_scores, umap_scores, cluster_labels, labeled_metadata)`

作用:

```text
Create the stable cell-level table used by final figures.
```

输入:

```text
feature_metadata with one row per sampled snapshot
pca_scores
umap_scores
cluster_labels
labeled_metadata with one row per run_id and presister_like
```

输出:

```text
cell_state_table
```

伪代码:

```text
function build_cell_state_table(feature_metadata, pca_scores, umap_scores, cluster_labels, labeled_metadata):
    1. start from feature_metadata with one row per run_id / state_recovery_time
    2. rename run_id to simulation_id if desired, or keep both
    3. merge PC1 and PC2 by feature row order
    4. merge UMAP1 and UMAP2 by feature row order
    5. merge cluster_id by feature row order
    6. merge presister_like and state_label from labeled_metadata by run_id
    7. set lag_time = the simulation-level recovery_time from labeled_metadata
    8. set recovered_label from recovered
    9. keep stable columns:
        - simulation_id
        - run_id
        - Tw
        - state_recovery_time
        - recovery_time
        - lag_time
        - recovered_label
        - cluster_id
        - presister_like
        - state_label
        - PC1
        - PC2
        - UMAP1
        - UMAP2
    10. return table sorted by Tw, run_id, state_recovery_time
```

代码类型标注:

```text
主干分析表构建
```

复杂度提醒:

```text
This table is the spine of the final plotting code.
Keep row identity checks simple and explicit.
```

### `compute_cycle_group_features(spins, cycle_starts, cycle_lengths)`

作用:

```text
For one cell/network, summarize spin activity by short/medium/long cycle groups.
```

输入:

```text
spin vector
cycle_starts
cycle_lengths
```

输出:

```text
short/medium/long cycle magnetization values for one cell
```

伪代码:

```text
function compute_cycle_group_features(spins, cycle_starts, cycle_lengths):
    1. compute cycle_magnetization for each cycle
    2. split cycle_lengths into lower/middle/upper thirds
    3. assign each cycle to short, medium, or long group
    4. average cycle_magnetization within each group
    5. return one row:
        - short_cycle_activation
        - medium_cycle_activation
        - long_cycle_activation
        - n_short_cycles
        - n_medium_cycles
        - n_long_cycles
```

代码类型标注:

```text
可选机制分析
```

复杂度提醒:

```text
Compute this while the current cell's network object is still in memory.
Do not try to compare cycle_id across cells.
The saved table should compare only short/medium/long summaries.
```

### `compute_cycle_pc1_moving_average(cell_state_table, cycle_group_table, window_size)`

作用:

```text
Prepare Fig. D moving-average table along PC1.
```

输入:

```text
cell_state_table with PC1
cycle_group_table with short/medium/long activation per cell
window_size
```

输出:

```text
cycle_pc1_moving_average table
```

伪代码:

```text
function compute_cycle_pc1_moving_average(cell_state_table, cycle_group_table, window_size):
    1. choose the state_recovery_time used for Fig. D, usually 0 min or the same state used for Fig. E
    2. filter cell_state_table and cycle_group_table to that state_recovery_time
    3. merge PC1 with cycle group features by simulation_id and state_recovery_time
    4. sort cells by PC1
    5. slide a moving window across sorted cells
    6. for each window:
        6.1 compute PC1_window_center
        6.2 compute mean and SEM for short cycle activation
        6.3 compute mean and SEM for medium cycle activation
        6.4 compute mean and SEM for long cycle activation
    7. return long-format table with:
        - PC1_window_center
        - cycle_group
        - mean_cycle_activation
        - sem_cycle_activation
        - n_cells_in_window
        - window_size
```

代码类型标注:

```text
可选机制分析
```

复杂度提醒:

```text
This is the selected Fig. D strategy.
Its interpretation is cycle-length group behavior, not shared-cycle identity.
```

### `run_final_state_analysis(simulation_data, params)`

作用:

```text
Coordinate PCA, UMAP, clustering, presister labels, and final analysis tables.
```

输入:

```text
simulation_data
params
```

输出:

```text
dictionary of final analysis tables
```

伪代码:

```text
function run_final_state_analysis(simulation_data, params):
    1. X_features, feature_metadata = build_spin_feature_matrix(simulation_data, params["feature_mode"])
    2. tail_fraction_table = load_tail_fraction_table(params["sourcefig2_path"], params["waiting_times"])
    3. pca_scores, explained_variance = run_pca(X_features, params["pca_components"], params["random_seed"])
    4. umap_scores = run_umap(pca_scores first N columns, params["random_seed"])
    5. cluster_labels = run_clustering(pca_scores first N columns, params["n_clusters"], params["random_seed"])
    6. labeled_metadata = assign_presister_like_by_tail_fraction(metadata, tail_fraction_table)
    7. cell_state_table = build_cell_state_table(feature_metadata, pca_scores, umap_scores, cluster_labels, labeled_metadata)
    8. recovery_dynamics = compute_recovery_dynamics_by_Tw(magnetization, metadata)
    9. cluster_summary = summarize_cluster_by_Tw(
        cell_state_table,
        params["state_recovery_time_for_cluster_summary"],
    )
    10. cycle_pc1_moving_average = compute_cycle_pc1_moving_average(
        cell_state_table,
        simulation_data["cycle_group_features"],
        params["figD_window_size"],
    )
    11. return all tables in a dictionary
```

代码类型标注:

```text
主干分析流程
```

复杂度提醒:

```text
This function should be readable from top to bottom as the final analysis workflow.
```

---

## File: `src/rccn_persistence/plotting.py`

General plotting rule:

```text
Plotting functions receive final tables and output paths.
They should not compute final labels or dimensionality reduction.
```

### `plot_figA_recovery_dynamics(recovery_dynamics, output_path)`

作用:

```text
Draw RCCN ageing reproduction curves.
```

输入:

```text
recovery_dynamics_by_Tw table
output_path
```

输出:

```text
figA PNG/SVG/PDF
```

伪代码:

```text
function plot_figA_recovery_dynamics(recovery_dynamics, output_path):
    1. create figure and axis
    2. for each Tw:
        2.1 select rows for Tw
        2.2 plot recovery_time vs mean_recovery_observable
        2.3 optionally add SEM band
    3. label x-axis "Recovery time after nutrient restoration (min)"
    4. label y-axis with chosen recovery observable
    5. add legend ordered by Tw
    6. add title
    7. save figure
```

代码类型标注:

```text
绘图逻辑
```

复杂度提醒:

```text
Keep annotation text in the figure caption/report, not as crowded plot text.
```

### `plot_figB_umap_by_Tw_recovery_time(cell_state_table, tail_fraction_table, output_path)`

作用:

```text
Draw three UMAP panels for selected Tw values colored by recovery time category.
```

输入:

```text
cell_state_table
tail_fraction_table
output_path
```

输出:

```text
figB
```

伪代码:

```text
function plot_figB_umap_by_Tw_recovery_time(cell_state_table, tail_fraction_table, output_path):
    1. selected_Tw = [0, 488, 1346]
    2. selected_recovery_times = [0, 20, 120]
    3. create one row of three panels
    4. use shared UMAP axis limits across panels
    5. for each selected Tw:
        5.1 select cells with this Tw
        5.2 require exact state_recovery_time categories 0, 20, 120
        5.3 if any category is missing, raise a clear error and rerun simulation with selected snapshots
        5.4 scatter UMAP1 vs UMAP2 colored by recovery_time_category
        5.5 title panel with Tw
        5.6 add tail fraction text below panel
    6. add shared legend
    7. save figure
```

代码类型标注:

```text
绘图逻辑
```

复杂度提醒:

```text
This figure requires the simulation extension that saves 0, 20, and 120 min snapshots.
Do not approximate Fig. B from a single release snapshot.
```

### `plot_figC_cluster_occupancy_and_lag(cluster_summary, cell_state_table, output_path, state_recovery_time_for_summary)`

作用:

```text
Draw cluster fraction by Tw and recovery-time distribution by cluster.
```

输入:

```text
cluster_summary_by_Tw
cell_state_table
output_path
state_recovery_time_for_summary
```

输出:

```text
figC
```

伪代码:

```text
function plot_figC_cluster_occupancy_and_lag(cluster_summary, cell_state_table, output_path, state_recovery_time_for_summary):
    1. create two-panel figure
    2. left panel:
        2.1 pivot cluster_summary to Tw x cluster_id fractions
        2.2 draw stacked bars
        2.3 label axes and legend
    3. right panel:
        3.1 filter cell_state_table to state_recovery_time_for_summary
        3.2 draw violin/box/jitter plot of recovery_time by cluster_id
        3.3 if recovery_time is heavy-tailed, use log scale or log10(recovery_time + 1)
    4. save figure
```

代码类型标注:

```text
绘图逻辑
```

复杂度提醒:

```text
Use matplotlib first. Add seaborn only if already available and helpful.
```

### `plot_figE_presister_like_pca_umap(cell_state_table, output_path, state_recovery_time_for_figE)`

作用:

```text
Draw PCA and UMAP panels colored by tail-fraction-defined state label.
```

输入:

```text
cell_state_table
output_path
state_recovery_time_for_figE
```

输出:

```text
figE
```

伪代码:

```text
function plot_figE_presister_like_pca_umap(cell_state_table, output_path, state_recovery_time_for_figE):
    1. filter cell_state_table to state_recovery_time_for_figE, usually 0 min
    2. create two-panel figure
    3. define plotting order:
        - normal first
        - presister-like second
    4. left panel:
        4.1 scatter PC1 vs PC2
        4.2 color by state_label
    5. right panel:
        5.1 scatter UMAP1 vs UMAP2
        5.2 color by same state_label
    6. use same colors in both panels
    7. add legend
    8. save figure
```

代码类型标注:

```text
绘图逻辑
```

复杂度提醒:

```text
This is a main figure. Make the table generation robust before tuning aesthetics.
```

### `plot_figD_cycle_groups_along_PC1(cycle_pc1_moving_average, cell_state_table, output_path)`

作用:

```text
Draw optional PC1 density and cycle-group moving average.
```

输入:

```text
cycle_pc1_moving_average
cell_state_table
output_path
```

输出:

```text
figD
```

伪代码:

```text
function plot_figD_cycle_groups_along_PC1(cycle_pc1_moving_average, cell_state_table, output_path):
    1. create two vertically stacked panels
    2. top panel:
        2.1 plot density or histogram of PC1
        2.2 optionally color by presister_like or Tw
    3. bottom panel:
        3.1 for each cycle_group:
            plot PC1_window_center vs mean_cycle_activation
            add SEM band if available
    4. label axes
    5. save figure
```

代码类型标注:

```text
可选绘图逻辑
```

复杂度提醒:

```text
Do not implement before cycle-group table is scientifically settled.
```

---

## File: `src/rccn_persistence/io_utils.py`

### `make_final_output_paths(project_root)`

作用:

```text
Define final simulation, analysis, and figure output directories.
```

输入:

```text
project_root
```

输出:

```text
paths dictionary
```

伪代码:

```text
function make_final_output_paths(project_root):
    1. project_root = Path(project_root)
    2. return:
        - final_simulation: output/final_simulation
        - final_analysis: output/final_analysis
        - final_figures: output/final_figures
```

代码类型标注:

```text
保存输出
```

复杂度提醒:

```text
Do not search for outputs automatically.
```

### `save_final_simulation_outputs(batch_result, paths)`

作用:

```text
Save simulation products required for Fig. A/C/E/B and Fig. D group summaries.
```

输入:

```text
batch_result
paths
```

输出:

```text
CSV and NPY files on disk
```

伪代码:

```text
function save_final_simulation_outputs(batch_result, paths):
    1. create final_simulation directory
    2. save metadata.csv
    3. save magnetization.csv
    4. save selected_spin_snapshots.npy
    5. save snapshot_metadata.csv
    6. save cycle_group_features.csv
    7. optionally save old compatibility files:
        - spin_release.npy
        - spin_early_recovery.npy
```

代码类型标注:

```text
保存输出
```

复杂度提醒:

```text
The selected_spin_snapshots.npy row order must match snapshot_metadata.csv exactly.
```

### `save_final_analysis_outputs(analysis_result, paths)`

作用:

```text
Save final analysis tables with stable filenames.
```

输入:

```text
analysis_result dictionary
paths
```

输出:

```text
CSV files on disk
```

伪代码:

```text
function save_final_analysis_outputs(analysis_result, paths):
    1. create final_analysis directory
    2. save tail_fraction_by_Tw.csv
    3. save recovery_dynamics_by_Tw.csv
    4. save cell_state_table.csv
    5. save pca_scores.csv
    6. save pca_explained_variance.csv
    7. save umap_scores.csv
    8. save cluster_summary_by_Tw.csv
    9. save recovery_time_by_cluster.csv if separate
    10. save cycle_group_features.csv
    11. save cycle_pc1_moving_average.csv
```

代码类型标注:

```text
保存输出
```

复杂度提醒:

```text
Explicit filenames are good here.
```

---

## 9. What to Reuse vs Rewrite

### Reuse directly

```text
network.py:
    sample_cycle_lengths
    make_cycle_starts
    choose_coupling_indices
    build_shift_edges
    build_intercycle_edges
    build_rccn_network

dynamics.py:
    initialize_spins
    sign_without_zero_problem
    update_spins_once
    run_one_protocol core update loop, then extend it to save selected recovery snapshots

observables.py:
    compute_cycle_magnetization
    compute_global_magnetization
    compute_baseline_magnetization
    compute_recovery_time
```

### Extend carefully

```text
simulation.py:
    add final params and required selected snapshot saving
    compute per-cell short/medium/long cycle group summaries while network metadata is available

io_utils.py:
    add final output path and save/load helpers

observables.py:
    add recovery dynamics table, tail fraction, presister-like labels
```

### Allowed to rewrite

```text
spin_analysis.py:
    old manual PCA/k-means flow can be replaced by a cleaner final state-analysis flow

plotting.py:
    old quick-look plotting functions can remain,
    but final figures should use new dedicated plotting functions
```

### Keep separate for clarity

```text
scripts/run_rccn_simulation.py
scripts/run_spin_clustering.py
scripts/make_project_figures.py
```

These can stay as first-version scripts.

Add final scripts instead of modifying all old scripts in place:

```text
scripts/run_final_rccn_simulation.py
scripts/run_final_state_analysis.py
scripts/make_final_project_figures.py
```

---

## 10. Suggested Implementation Order

### Step 1: Final parameter preset

```text
Add make_final_project_params()
Run a small validation with Tw = [0, 195, 488] and n_runs = 5.
Set selected_recovery_times = [0, 20, 120].
```

### Step 2: Tail fraction table

```text
Load sourcefig2.xlsx.
Create tail_fraction_by_Tw.csv.
Confirm Tw = 1500 extrapolation.
```

### Step 3: Simulation output extensions

```text
Extend run_one_protocol() to save selected snapshots at 0, 20, 120 min after release.
Save selected_spin_snapshots.npy.
Save snapshot_metadata.csv.
While each cell's network is still available, compute short/medium/long cycle group magnetization.
Save cycle_group_features.csv.
```

### Step 4: Final analysis table

```text
Build feature matrix from selected_spin_snapshots.npy.
Run PCA.
Run UMAP.
Run clustering.
Assign presister-like labels.
Save cell_state_table.csv.
Save cluster_summary_by_Tw.csv.
Save cycle_pc1_moving_average.csv.
```

### Step 5: Core figures in requested order

```text
Implement Fig. A: recovery dynamics.
Implement Fig. C: cluster occupancy and lag distribution.
Implement Fig. E: presister-like PCA and UMAP.
Implement Fig. B: UMAP by Tw and recovery time.
These four figures should not be simplified by missing data products; add the required data outputs instead.
```

### Step 6: Fig. D group-summary version

```text
Implement Fig. D after A/C/E/B are running.
Use the per-cell cycle group summary strategy:
    - short cycles mean magnetization
    - medium cycles mean magnetization
    - long cycles mean magnetization
Do not compare concrete cycle_id across cells.
```

---

## 11. Tests and Sanity Checks

Recommended small tests:

```text
test_tail_fraction_direct_and_extrapolated_rows()
test_presister_like_fraction_within_each_Tw()
test_selected_snapshots_have_exact_recovery_times_0_20_120()
test_cell_state_table_has_one_row_per_sampled_state()
test_cluster_summary_fractions_sum_to_one_within_Tw()
test_recovery_dynamics_recovery_time_starts_at_zero()
test_cycle_group_features_have_short_medium_long_columns()
```

Recommended visual/data sanity checks:

```text
1. snapshot_metadata row count equals n_metadata_rows * len(selected_recovery_times)
2. selected_spin_snapshots row count equals snapshot_metadata row count
3. cell_state_table row count equals snapshot_metadata row count
4. every run_id appears once for each state_recovery_time
5. cluster fractions sum to 1 within each Tw
6. presister_like fraction approximately matches TailFraction within each Tw
7. PCA and UMAP tables have no missing coordinates
8. Fig. A curves are ordered or at least visibly Tw-dependent
9. Fig. B contains exact 0, 20, and 120 min recovery-time categories
10. Fig. D uses only cycle-length groups, not shared cycle_id
```

---

## 12. Open Scientific Decisions Before Full Coding

These do not block writing the first implementation, but they should be explicit:

1. Feature representation:

```text
release only vs early only vs release + early
```

Recommended:

```text
release + early as primary; release-only as sensitivity check.
```

2. UMAP input:

```text
raw spin features vs first N PCs
```

Recommended:

```text
first 10 PCs, because raw spin dimension is large and noisy.
```

3. Cluster number:

```text
K = 3 or K = 4
```

Recommended:

```text
start with K = 3 to match current code; inspect whether slow-recovery cells form a stable cluster.
```

4. Tw = 1500 tail fraction extrapolation:

```text
linear vs logit-linear
```

Recommended:

```text
linear first, with value clipped to [0, 1], unless the source values are near boundary.
```

5. Fig. B recovery-time snapshots:

```text
Current simulation saves release and early recovery only.
Final requirement asks 0, 20, 120 min.
```

Recommended:

```text
Extend run_one_protocol() to save selected recovery snapshots at [0, 20, 120].
This is required for the final Fig. B plan; do not substitute nearest snapshots.
```

6. Fig. D cycle interpretation:

```text
Current per-cell networks make cycle_id not globally comparable.
```

Recommended:

```text
Use short/medium/long cycle-group summaries per cell.
Each cell may keep its own random RCCN network.
The valid comparison is group-level mean magnetization, not shared cycle identity.
```

---

## 13. Summary

The current simulation core is worth preserving. The final project mainly needs a clearer analysis layer and a dedicated final plotting layer.

The safest refactor direction is:

```text
Keep RCCN simulation functions.
Add final-project parameters and final output directories.
Extend simulation outputs to save selected recovery snapshots at 0, 20, and 120 min.
Rewrite spin_analysis.py around a stable cell_state_table.
Add tail-fraction-derived presister-like labels.
Add UMAP and final figure plotting functions.
Implement Fig. A/C/E/B first with required data products.
Implement Fig. D afterward using per-cell short/medium/long cycle group summaries.
```

This keeps the code as scientific analysis code rather than a large software framework, while giving the final report the data products and figures requested in the plotting requirements.

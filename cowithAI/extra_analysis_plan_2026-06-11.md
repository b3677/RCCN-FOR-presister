# Extra analysis plan: tail-fraction cluster matching and refined loop-length activity

Date: 2026-06-11

This plan follows the Scientific Code Scholar style: clarify the scientific
question, define what can be done from existing data, list decisions that need
confirmation, then give implementation-level pseudocode before writing code.

The two proposed extra analyses are:

1. Match experimental tail fraction vs `Tw` to RCCN cluster fractions.
2. Refine Fig. D loop-length activity beyond the current short / medium / long
   grouping.

Spin covariance is intentionally excluded for now.

## 1. Current scientific goal

The main project asks whether ageing / stress waiting time `Tw` reshapes the
RCCN high-dimensional spin-state landscape and creates a small slow-recovering
or persister-like population.

The extra analyses should strengthen two claims:

1. A small RCCN state-space population may correspond to the experimental
   persister tail fraction.
2. Recovery-associated state directions may be driven by specific loop-length
   scales, especially medium-length loops.

## 2. Existing data available

No new simulation is required.

Use existing final simulation and analysis outputs:

```text
output/result611/final_simulation/
output/result611/final_analysis/
```

Key inputs:

```text
output/result611/final_analysis/cell_state_table.csv
output/result611/final_analysis/cluster_summary_by_Tw.csv
output/result611/final_analysis/tail_fraction_by_Tw.csv
output/result611/final_analysis/cycle_group_features.csv
output/result611/final_simulation/selected_spin_snapshots.npy
output/result611/final_simulation/snapshot_metadata.csv
output/result611/final_simulation/metadata.csv
output/result611/final_simulation/params.json
data/sourcefig2.xlsx
```

Current direct experimental tail-fraction points in `sourcefig2.xlsx`:

```text
Tw = 0, 195, 488, 1346
```

Current extrapolated point used by the final analysis:

```text
Tw = 1500
```

## 3. Decisions needing user confirmation

### A. Tail-fraction fitting

Need to confirm how aggressive the fit should be.

Recommended default:

```text
Fit simple monotonic / low-parameter curves only.
Use the fit as descriptive support, not as a mechanistic law.
```

Candidate models:

1. Linear fit on raw fraction:

   ```text
   TailFraction = a + b * Tw
   ```

   Pros: transparent.
   Cons: may behave poorly outside observed range.

2. Linear fit on log fraction:

   ```text
   log(TailFraction) = a + b * Tw
   ```

   Pros: better for small positive fractions.
   Cons: assumes approximately exponential growth of tail fraction.

3. Logistic / saturating curve:

   ```text
   TailFraction = L / (1 + exp(-(a + b * Tw)))
   ```

   Pros: bounded between 0 and 1.
   Cons: 4 direct points are too few for a flexible fit.

Default recommendation:

```text
Use raw-point plotting plus a simple log-linear fit.
Do not over-interpret the fitted curve.
```

Need user confirmation:

```text
Use log-linear tail-fraction fit as the default?
```

### B. Cluster matching search space

Need to confirm whether to use existing final `K=3` clusters only, or rerun
clustering on existing PC scores for multiple `K`.

Recommended default:

```text
Try K = 3, 4, 5, 6, 8, 10 using existing PC1-PC10 scores.
No new simulation and no new PCA are needed.
```

Why:

- Experimental tail fraction is very small: about 0.002 to 0.047.
- Existing `K=3` clusters may be too coarse.
- Re-clustering PC scores is cheap and directly tests whether a small state
  population exists.

Need user confirmation:

```text
Search K = 3, 4, 5, 6, 8, 10?
```

### C. Matching criterion

Need to confirm what counts as a good tail-matching RCCN population.

Recommended default:

Score each candidate cluster by:

```text
RMSE between cluster_fraction(Tw) and TailFraction(Tw)
Spearman correlation between cluster_fraction(Tw) and TailFraction(Tw)
slow-recovery enrichment within the cluster
presister_like enrichment within the cluster
```

Do not select purely by RMSE if the cluster is not slow-recovering.

Need user confirmation:

```text
Require the best-matching cluster to also have above-average lag time or
presister_like enrichment?
```

### D. Single cluster vs cluster combination

Need to confirm whether a candidate RCCN tail population can be:

```text
one cluster
or a combination of several small clusters
```

Recommended default:

```text
First report single-cluster matches.
Then optionally report best two-cluster combinations as exploratory.
```

Reason:

- Single-cluster interpretation is cleaner.
- Cluster combinations can overfit with only 5 `Tw` points.

Need user confirmation:

```text
Include two-cluster combinations as exploratory backup?
```

### E. Loop-length bin definition

Need to confirm how to subdivide loops.

Current final analysis only saved:

```text
short / medium / long cycle activation
```

For more detailed bins, we need to reconstruct each run's network cycle lengths
from deterministic seeds and recompute loop-bin activity from saved snapshots.

Recommended default:

Use quantile bins of cycle length within each cell/network:

```text
5 bins: Q1, Q2, Q3, Q4, Q5
```

Alternative:

Use absolute length bins:

```text
1-5
6-20
21-100
101-500
>500
```

Default recommendation:

```text
Use both, but make quantile bins the main analysis.
```

Why:

- Quantile bins ensure each simulated network contributes to every bin.
- Absolute bins are more physically interpretable but may be uneven or empty.

Need user confirmation:

```text
Use 5 quantile bins as main and absolute bins as supplementary?
```

### F. Which snapshot time to emphasize

The final analysis has selected recovery snapshots:

```text
0, 250, 500, 1000, 2000, 4000
```

Recommended default:

```text
Use state_recovery_time = 0 for main loop-bin analysis.
Also provide a heatmap across all six recovery times.
```

Reason:

- `state_recovery_time = 0` is the release state and matches current Fig. D logic.
- Recovery-time heatmap shows whether the medium-loop effect persists or changes.

Need user confirmation:

```text
Use state_recovery_time = 0 as the main panel?
```

## 4. Analysis 1: Tail fraction vs RCCN cluster fraction

### Scientific question

Does the RCCN state-space analysis contain a small cell-state population whose
occupancy increases with `Tw` similarly to the experimental tail fraction?

### Inputs

```text
cell_state_table.csv
tail_fraction_by_Tw.csv
```

Use only one row per simulated cell for cluster occupancy, usually:

```text
state_recovery_time == 0
```

### Outputs

Directory:

```text
output/ex_analysis/tail_fraction_cluster_matching
```

Tables:

```text
tail_fraction_fit.csv
cluster_match_scores.csv
cluster_fraction_by_Tw_by_K.csv
best_cluster_cell_summary.csv
```

Figures:

```text
tail_fraction_fit.png
best_cluster_fraction_vs_tail_fraction.png
best_cluster_umap.png
cluster_match_score_heatmap.png
```

### Pseudocode

```text
load cell_state_table
load tail_fraction_by_Tw

select rows where state_recovery_time == 0

fit tail fraction vs Tw:
    raw points
    log-linear fit
    predicted tail fraction for target Tw values

for each K in selected K values:
    cluster existing PC1-PC10 scores using KMeans
    compute cluster_fraction(Tw, cluster_id)
    compute mean_lag_time and presister_like enrichment for each cluster
    compare cluster_fraction(Tw) to TailFraction(Tw)
    store RMSE, correlation, lag enrichment, presister enrichment

rank clusters:
    prefer low RMSE
    prefer positive correlation
    prefer slow-recovery or presister-like enrichment

save tables
plot best match
plot UMAP colored by best-matching cluster
```

### Interpretation rule

A good candidate cluster should not merely match the fraction numerically. It
should also show biological/model relevance:

```text
longer lag time
or higher presister_like fraction
or clear state-space localization
```

## 5. Analysis 2: Refined loop-length bin activity

### Scientific question

Which loop-length scales contribute most strongly to the recovery-associated
state direction, especially PC1 and lag-time variation?

### Inputs

```text
selected_spin_snapshots.npy
snapshot_metadata.csv
metadata.csv
cell_state_table.csv
params.json
```

Need to reconstruct network cycle lengths for each `run_id` using the same
deterministic seed logic as final simulation:

```text
make_run_seed(base_seed, Tw, run_id)
build_rccn_network(params, rng)
```

Then compute cycle magnetization from saved snapshots:

```text
cycle_mags = mean spin within each cycle
loop-bin activation = mean cycle_mags within each loop-length bin
```

### Outputs

Directory:

```text
output/ex_analysis/loop_length_bins
```

Tables:

```text
loop_bin_activity_long.csv
loop_bin_activity_by_PC1_window.csv
loop_bin_activity_by_Tw.csv
loop_bin_correlation_summary.csv
```

Figures:

```text
loop_bin_activity_along_PC1.png
loop_bin_activity_by_Tw_heatmap.png
loop_bin_activity_by_recovery_time_heatmap.png
loop_bin_correlation_with_lag_time.png
```

### Pseudocode

```text
load params
load selected_spin_snapshots as mmap
load snapshot_metadata
load cell_state_table

for each run_id:
    read Tw from metadata
    reconstruct rng seed using make_run_seed(random_seed, Tw, run_id)
    rebuild RCCN network
    get cycle_starts and cycle_lengths
    assign cycles to loop-length bins

for each saved snapshot row:
    get run_id and state_recovery_time
    get corresponding cycle_starts, cycle_lengths, bin labels
    compute cycle magnetization
    compute mean activation for each bin
    save long-form table:
        run_id
        Tw
        state_recovery_time
        bin_id
        bin_label
        mean_cycle_activation
        n_cycles
        PC1
        lag_time
        presister_like

main summaries:
    by PC1 sliding window
    by Tw
    by state_recovery_time
    correlation with lag_time
    correlation with PC1

save tables and figures
```

### Complexity

This does not rerun spin dynamics.

It reconstructs networks and computes cycle summaries from existing snapshots.
Approximate workload:

```text
10000 runs
60000 snapshots
16384 spins per snapshot
```

This is feasible, but should be written carefully with streaming / chunked
processing so it does not build unnecessary huge intermediate arrays.

## 6. Proposed script

New script:

```text
scripts/run_extra_analysis.py
```

Command:

```powershell
C:\work\env_rccn_stable\python.exe scripts\run_extra_analysis.py
```

Optional switches:

```powershell
--tail-cluster
--loop-bins
--output-dir output\ex_analysis
--state-recovery-time 0
--k-values 3 4 5 6 8 10
```

Default:

```text
Run both tail-cluster matching and loop-bin analysis.
Write all outputs to output/ex_analysis.
```

## 7. Recommended next decision

Recommended defaults unless the user changes them:

```text
Tail fit: log-linear plus raw points
Cluster search: K = 3, 4, 5, 6, 8, 10
Cluster matching: require fraction similarity plus slow-recovery enrichment
Cluster combinations: report single clusters first, two-cluster combinations optional
Loop bins: 5 quantile bins main, absolute bins supplementary
Main snapshot: state_recovery_time = 0
Extra loop heatmap: all selected recovery times
Output root: output/ex_analysis
```

After the user confirms these choices, implement `scripts/run_extra_analysis.py`.


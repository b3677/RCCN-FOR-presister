# RCCN persistence ageing final project: main-figure plotting requirements

## 0. Purpose of this document

This document converts the planned “style-similar-to-paper” figures into precise plotting requirements for the final project.

The goal is **not** to implement code here. The goal is to define, for each figure:

1. what scientific question the figure should answer;
2. which published figure it is inspired by;
3. what the final plot should look like;
4. what quantities must be available to draw it;
5. what annotations and labels should be included.

The project uses the RCCN / spin-glass model from Yoav Kaplan et al., *Observation of universal ageing dynamics in antibiotic persistence*, and compares model-generated single-cell spin states to the single-cell state logic in Sydney B. Blattman et al., *Identification and genetic dissection of convergent persister cell states*.

---

## 1. Global plotting assumptions

### 1.1 Time convention

The original published RCCN numerical simulation code does not include an explicit conversion between simulation updates and physical time. The published figures use the discrete update step directly as the time axis.

For this project, use the same convention:

```text
1 simulation step ≈ 1 min
```

All axes shown in minutes should therefore be interpreted as simulation-step units displayed as minutes.

### 1.2 Waiting times to simulate

Use exactly the following five starvation / waiting times:

```text
Tw = 0, 195, 488, 1346, 1500 min
```

The first four values correspond to points for which Fig. 2c-like tail-fraction data are available from Yoav Kaplan et al. The value `Tw = 1500 min` should be assigned a tail fraction by fitting / extrapolating the existing Fig. 2c source data.

Source data file for tail fraction:

```text
F:\aging_code\homework\q-bio_homework\qbio_final_project\data\sourcefig2.xlsx
```

Required columns:

```text
Tw_minutes
TailFraction
TailFractionSTD
```

### 1.3 Simulation scale

Use a small parameter-search / validation run first to verify the full plotting pipeline. After selecting one acceptable parameter combination, run the large-scale simulation:

```text
n = 900 simulations per Tw
```

The plotting code should be written so that the same plotting functions can be used for both the small validation run and the final `n = 900` run.

### 1.4 Cell-level data unit

Each simulated trajectory should be treated as one model “single cell”. For dimensionality reduction, clustering, and recovery-time classification, the unit of analysis is:

```text
one simulated trajectory at a given Tw and recovery time
```

### 1.5 Recommended cell-state representation

For PCA / UMAP / clustering, represent each simulated cell by a spin-state feature vector. The exact representation should be decided in the implementation stage, but the plotting requirements assume that each simulated cell can be assigned:

```text
Tw
recovery_time
simulation_id
spin_state_vector or cycle-averaged spin/magnetization features
lag_time or recovery_time_to_growth
cluster_id
presister_like label
normal label
```

---

## 2. Proposed main figure set

The current recommended main-figure set contains five figures:

| Figure | Working title | Core role in project | Main / optional |
|---|---|---|---|
| Fig. A | RCCN ageing reproduction | Show that the RCCN model can reproduce waiting-time-dependent recovery ageing | Main |
| Fig. B | UMAP of simulated spin states at selected Tw | Ask whether simulated spin states form Blattman-like recovering / slow-recovering structure | Main |
| Fig. C | Cluster occupancy and lag distribution | Connect spin-state clusters to increasing slow-recovery occupancy and lag behavior | Main, but right panel can be auxiliary |
| Fig. D | Cycle-length groups along PC1 | Interpret model internal structure by asking whether cycle groups vary smoothly along a state axis | Optional / mechanistic |
| Fig. E | Presister-like vs normal cells in PCA and UMAP | Directly test whether tail-fraction-defined presister-like cells separate from normal cells | Main or backup main |

Recommended order in the final report:

```text
Fig. A → Fig. B → Fig. C → Fig. E → Fig. D
```

Reason: first prove the model runs and reproduces the original ageing effect, then inspect single-cell state geometry, then quantify cluster occupancy, then show the binary presister-like separation, and finally use PC1 / cycle structure as mechanistic interpretation.

---

# Fig. A. RCCN ageing reproduction

## Reference figure

Yoav Kaplan et al., *Observation of universal ageing dynamics in antibiotic persistence*, Fig. 3b.

## Scientific / project purpose

This figure should demonstrate that the current Python implementation can reproduce the core RCCN model behavior: recovery dynamics depend on starvation waiting time `Tw`, and longer `Tw` produces slower / broader recovery dynamics.

This is the “model validation” figure. It answers:

```text
Can our implementation reproduce the published RCCN ageing-like recovery dynamics before we use it for new single-cell state analysis?
```

## Plot structure

Use one multi-line plot or a small multi-panel plot showing recovery dynamics for the five waiting times:

```text
Tw = 0, 195, 488, 1346, 1500 min
```

Preferred version:

- x-axis: recovery time after nutrient / environment restoration, displayed in minutes;
- y-axis: population-averaged recovery observable;
- one curve per `Tw`;
- color encodes `Tw`, ordered from short to long waiting time;
- include a legend showing the five `Tw` values.

The recovery observable should follow the original RCCN model as closely as possible. Prefer the published RCCN quantity if available from the implemented code, for example:

```text
population-averaged magnetization / growth-state proxy / recovery fraction
```

If the implementation already defines a scalar “recovered / growing” state, the y-axis can be:

```text
fraction of simulations recovered
```

or

```text
mean cycle-averaged magnetization
```

The final choice should be explicitly written in the plot title or y-axis label.

## Required quantities

| Quantity | Meaning |
|---|---|
| `Tw` | waiting time before recovery simulation starts |
| `recovery_time` | time after recovery begins, in simulation steps displayed as min |
| `simulation_id` | trajectory identity |
| `recovery_observable` | scalar recovery / magnetization / growth-state proxy for each trajectory and time point |
| `mean_recovery_observable` | mean over simulations at each `Tw` and recovery time |
| `sem_or_std` | optional uncertainty band across simulations |

## Required annotations

- Title should clearly say this is an RCCN reproduction / validation plot.
- Add a note in the figure caption:

```text
Following the original RCCN code convention, 1 simulation step is displayed as approximately 1 min.
```

- If uncertainty bands are used, state whether they show standard deviation, standard error, or confidence intervals.

## Success criterion

This figure is successful if curves for longer `Tw` show slower recovery / delayed return / broader relaxation relative to shorter `Tw`, consistent with ageing-like recovery dynamics.

---

# Fig. B. UMAP of simulated spin states at selected waiting times

## Reference figure

Sydney B. Blattman et al., Fig. 1d.

The reference logic is that single-cell transcriptomes sampled before and after dilution into fresh medium are shown on UMAP. Cells are colored by recovery / dilution time, and the emergence of a distinct persister-like population is visible after the transition to hyper-persistence.

## Scientific / project purpose

This figure asks whether RCCN simulated single-cell spin states form a low-dimensional structure resembling the single-cell state separation observed in scRNA-seq.

It answers:

```text
Do model-generated spin states at different starvation times occupy different regions of state space during recovery?
```

and more specifically:

```text
At long Tw, do slow-recovering / persister-like cells form a visibly distinct region or branch in UMAP space?
```

## Plot structure

Make three separate UMAP panels, one for each selected waiting time:

```text
Tw = 0 min
Tw = 488 min
Tw = 1346 min
```

Each panel contains simulated cells from the same `Tw`, sampled at three recovery times:

```text
recovery_time = 0 min
recovery_time = 20 min
recovery_time = 120 min
```

Within each panel:

- x-axis: UMAP1;
- y-axis: UMAP2;
- each point: one simulated cell / trajectory state;
- color: recovery time category (`0`, `20`, `120 min`);
- use the same UMAP coordinate system for all three panels if possible, so panels are comparable;
- keep axis limits consistent across the three panels;
- point size should be small enough to show density but large enough to see overlap.

Below each panel, write the tail fraction for that `Tw`:

```text
Tail fraction = value ± STD
```

For `Tw = 1346`, use the value directly from the source Fig. 2c data. If `Tw = 1500` is not shown in this figure, no extrapolated value is needed here.

## Required quantities

| Quantity | Meaning |
|---|---|
| `Tw` | one of 0, 488, 1346 min |
| `recovery_time` | one of 0, 20, 120 min |
| `simulation_id` | trajectory identity |
| `spin_state_features` | feature vector used for UMAP |
| `UMAP1`, `UMAP2` | low-dimensional coordinates |
| `TailFraction` | tail fraction from Fig. 2c source data for this Tw |
| `TailFractionSTD` | uncertainty of tail fraction |

## Required annotations

Each panel title:

```text
Tw = 0 min
Tw = 488 min
Tw = 1346 min
```

Legend:

```text
Recovery time after nutrient restoration
0 min
20 min
120 min
```

Panel bottom text:

```text
Tail fraction = x.xx ± y.yy
```

## Success criterion

This figure is successful if the UMAP geometry changes with `Tw`, especially if long `Tw` shows delayed movement or partial separation between early recovery and late recovery states.

A clear separate island is not required; a continuous trajectory or branch is also scientifically meaningful.

---

# Fig. C. Cluster occupancy and lag distribution by cluster

## Reference figures

- Left panel style: Yoav Kaplan et al., Fig. 2f-like cluster occupancy / fraction plot.
- Conceptual comparison: Sydney B. Blattman et al., Fig. 2f, where persister cluster occupancy is quantified across different persistence models.
- Right panel style: lag / recovery-time distribution by state or cluster.

## Scientific / project purpose

This figure connects unsupervised spin-state clusters to the ageing phenotype.

It asks:

```text
As Tw increases, does a particular slow-recovery cluster become more occupied?
```

and:

```text
Do cells assigned to that cluster show longer recovery / lag times?
```

This is the key bridge between geometry and phenotype: the UMAP / clustering should not just look pretty; the clusters should have interpretable recovery behavior.

---

## Fig. C left: cluster fraction vs Tw

### Plot structure

Use a stacked bar plot or grouped bar plot.

Preferred version:

- x-axis: waiting time `Tw`;
- y-axis: fraction of simulations in each spin-state cluster;
- color: cluster identity;
- one stacked bar per `Tw`;
- fractions in each bar sum to 1.

Alternative version:

- grouped bars with one cluster per color and one group per `Tw`.

The stacked bar plot is recommended because it directly shows how total population composition changes with waiting time.

### Required quantities

| Quantity | Meaning |
|---|---|
| `Tw` | waiting time, all five values: 0, 195, 488, 1346, 1500 min |
| `simulation_id` | trajectory identity |
| `cluster_id` | unsupervised spin-state cluster assignment |
| `cluster_fraction` | fraction of simulations assigned to each cluster at each Tw |
| `slow_recovery_cluster_id` | cluster interpreted as slow-recovery / persister-like, if identifiable |

### Required annotations

- x-axis label:

```text
Waiting time Tw (min)
```

- y-axis label:

```text
Fraction of simulations
```

- legend title:

```text
Spin-state cluster
```

- optionally mark the slow-recovery cluster in the legend, for example:

```text
Cluster 2 (slow-recovery)
```

### Success criterion

This panel is successful if one or more clusters systematically increase or decrease with `Tw`. The most important expected pattern is that a slow-recovery / persister-like cluster increases at longer `Tw`.

---

## Fig. C right: recovery-time distribution by cluster

### Plot structure

Use one of the following, in order of preference:

1. violin plot + inner boxplot;
2. boxplot + jittered points;
3. cumulative distribution curves.

Recommended axes:

- x-axis: cluster identity;
- y-axis: recovery time / lag time;
- color: cluster identity or `Tw`.

If the distribution is broad or heavy-tailed, use either:

```text
log10(recovery time + 1)
```

or show the y-axis on a log scale.

### Required quantities

| Quantity | Meaning |
|---|---|
| `simulation_id` | trajectory identity |
| `Tw` | waiting time |
| `cluster_id` | cluster assignment |
| `lag_time` or `recovery_time_to_growth` | scalar recovery time for each trajectory |
| `presister_like` | optional binary label from tail-fraction threshold |

### Important note

If presister-like cells are already defined directly from Yoav Kaplan et al. Fig. 2c tail fraction, then this right panel may partially duplicate the tail-fraction logic. It is still useful as a sanity check:

```text
Does the cluster labelled slow-recovery actually have longer simulated lag times?
```

Therefore, treat this panel as useful but lower priority than the left cluster occupancy panel.

### Success criterion

This panel is successful if the cluster that increases with `Tw` also shows longer recovery / lag times than other clusters.

---

# Fig. D. Cycle-length groups along PC1

## Reference figure

Sydney B. Blattman et al., Fig. 3c.

The reference figure computes PC1 within the persister-related state space and then plots moving-average pathway expression along PC1. The key visual logic is not the exact biology of gene pathways, but the idea of using a one-dimensional state axis to interpret gradual internal differences within a persister-like state.

## Scientific / project purpose

This figure provides a mechanistic interpretation of the RCCN model. Instead of gene-expression pathways, use RCCN network-cycle groups.

It asks:

```text
Along the major spin-state axis PC1, do short, medium, and long feedback cycles show different average activation / magnetization patterns?
```

This connects the model’s internal network architecture to the observed ageing / recovery state.

## Plot structure

Use a two-part figure inspired by Blattman Fig. 3c.

### Top panel: density / distribution along PC1

- x-axis: PC1 score;
- y-axis: density or cell count;
- color or line type: optional group, such as `Tw` or presister-like label;
- purpose: show where simulated cells lie along the main state axis.

### Bottom panel: moving average along PC1

- x-axis: PC1 score;
- y-axis: mean activation / magnetization;
- one line per cycle-length group:
  - short cycles;
  - medium cycles;
  - long cycles.

Cycle groups should be defined by cycle length in the RCCN network. Exact cutoffs should be chosen explicitly before plotting. A reasonable requirement is:

```text
short cycles = lower third of cycle lengths
medium cycles = middle third of cycle lengths
long cycles = upper third of cycle lengths
```

or fixed cutoffs if biologically / computationally motivated.

The moving average should be computed over cells ordered by PC1 score. The window size should be stated in the caption, for example:

```text
moving average window = 100 cells
```

For small validation runs, use a smaller window. For final `n = 900`, choose a smoother window appropriate to the number of cells.

## Required quantities

| Quantity | Meaning |
|---|---|
| `simulation_id` | trajectory identity |
| `Tw` | waiting time |
| `recovery_time` | recovery time if multiple time points are included |
| `spin_state_features` | feature vector for PCA |
| `PC1` | first principal component score |
| `cycle_id` | identity of each RCCN cycle |
| `cycle_length` | number of nodes / spins in the cycle |
| `cycle_group` | short / medium / long |
| `cycle_activation` or `cycle_magnetization` | average spin activation / magnetization for each cycle in each cell |
| `moving_average_value` | smoothed mean along PC1 |

## Required annotations

- Title:

```text
RCCN cycle activity along PC1 state axis
```

- x-axis:

```text
PC1 score
```

- y-axis for bottom panel:

```text
Mean cycle activation / magnetization
```

- legend:

```text
Short cycles
Medium cycles
Long cycles
```

- caption must state how cycle groups were defined.

## Success criterion

This figure is successful if the PC1 axis has interpretable internal structure, for example long cycles becoming more activated / less recovered in the slow-recovery region. Even a negative result is useful: it would suggest that the observed slow-recovery state is not simply explained by cycle length.

---

# Fig. E. Tail-fraction-defined presister-like vs normal cells in PCA and UMAP

## Reference figures

- Yoav Kaplan et al., Fig. 1f / Extended Data Fig. 1n-style state-space visualization.
- Sydney B. Blattman et al., Fig. 1f / Extended Data Fig. 1n logic: an atlas of cell states shown by clustering, with PCA/UMAP used to show that persister cells occupy a distinct or transitional state.

## Scientific / project purpose

This figure is the most direct test of whether the RCCN spin-state space contains a presister-like state.

The idea is to define presister-like cells from the experimentally motivated tail fraction, rather than from unsupervised clustering alone.

It answers:

```text
If we define the slowest-recovering fraction of simulated cells at each Tw as presister-like, do these cells occupy a distinct region in PCA / UMAP space?
```

This figure is especially important because it avoids the circular logic of first clustering and then calling one cluster “persister”. Instead, the binary label is defined from recovery-time tail fraction derived from Yoav Kaplan et al. Fig. 2c.

## Presister-like definition

For each `Tw`, use the corresponding `TailFraction` value to define the slowest-recovering cells as presister-like.

For example, within each `Tw` group:

```text
presister-like cells = cells with recovery_time in the top TailFraction fraction
normal cells = all remaining cells
```

For `Tw = 1500`, use a fitted / extrapolated `TailFraction` from the Fig. 2c source data.

This definition should be applied separately within each `Tw`, not globally across all `Tw`, unless otherwise explicitly justified.

## Plot structure

Create one figure with two side-by-side panels:

```text
left: PCA
right: UMAP
```

### Left panel: PCA

- x-axis: PC1;
- y-axis: PC2;
- each point: one simulated cell / trajectory;
- color: binary state label:
  - normal;
  - presister-like;
- optionally use alpha blending so dense normal cells do not hide rare presister-like cells;
- plot presister-like cells on top of normal cells.

### Right panel: UMAP

- x-axis: UMAP1;
- y-axis: UMAP2;
- each point: one simulated cell / trajectory;
- color: same binary state label;
- use the same cell subset as the PCA panel;
- plot presister-like cells on top.

## Required quantities

| Quantity | Meaning |
|---|---|
| `simulation_id` | trajectory identity |
| `Tw` | waiting time, all five values: 0, 195, 488, 1346, 1500 min |
| `recovery_time_to_growth` or `lag_time` | scalar used to rank cells within each Tw |
| `TailFraction` | tail fraction for each Tw |
| `TailFractionSTD` | optional uncertainty from source data |
| `presister_like` | binary label assigned from tail-fraction rule |
| `spin_state_features` | features used for PCA / UMAP |
| `PC1`, `PC2` | PCA coordinates |
| `UMAP1`, `UMAP2` | UMAP coordinates |

## Required annotations

- Main title:

```text
Tail-fraction-defined presister-like cells in RCCN state space
```

- Legend:

```text
Normal
Presister-like
```

- Caption should explicitly state:

```text
Presister-like cells were defined as the slowest-recovering TailFraction fraction within each Tw group, using Fig. 2c-derived tail fractions.
```

- If `Tw = 1500` is included, caption should state:

```text
TailFraction for Tw = 1500 min was extrapolated from the Fig. 2c source data.
```

## Success criterion

This figure is successful if presister-like cells are enriched in a distinct or transitional region of PCA / UMAP space. A perfect separate cluster is not required. A gradient or edge enrichment is also meaningful and may better match a continuous ageing landscape.

---

# 3. Data products required before plotting

Codex should assume that the plotting stage requires the following analysis tables. The exact file format can be CSV or Parquet, but column names should be explicit and stable.

## 3.1 Cell-level state table

One row per simulated cell / trajectory / sampled recovery time.

Required columns:

```text
simulation_id
Tw
recovery_time
spin_state_features or path to feature matrix row
lag_time
recovered_label
cluster_id
presister_like
PC1
PC2
UMAP1
UMAP2
```

Notes:

- `cluster_id`, `presister_like`, `PC1`, `PC2`, `UMAP1`, and `UMAP2` may be generated after initial simulation.
- If feature vectors are high-dimensional, store them separately as a matrix, but keep row identity linked by `simulation_id`, `Tw`, and `recovery_time`.

## 3.2 Recovery dynamics table

One row per `Tw` and recovery time.

Required columns:

```text
Tw
recovery_time
mean_recovery_observable
std_recovery_observable
sem_recovery_observable
n_simulations
```

Used for Fig. A.

## 3.3 Tail-fraction table

One row per `Tw`.

Required columns:

```text
Tw
TailFraction
TailFractionSTD
TailFraction_source
```

`TailFraction_source` should distinguish:

```text
sourcefig2_direct
sourcefig2_extrapolated
```

Used for Fig. B annotations and Fig. E presister-like definition.

## 3.4 Cluster summary table

One row per `Tw` and `cluster_id`.

Required columns:

```text
Tw
cluster_id
n_cells
cluster_fraction
mean_lag_time
median_lag_time
```

Optional columns:

```text
presister_like_fraction
mean_PC1
mean_PC2
```

Used for Fig. C.

## 3.5 Cycle PC1 moving-average table

One row per PC1 window and cycle group.

Required columns:

```text
PC1_window_center
cycle_group
mean_cycle_activation
sem_cycle_activation
n_cells_in_window
window_size
```

Used for Fig. D.

---

# 4. Recommended final figure naming

Save final figures with stable filenames:

```text
figA_rccn_ageing_reproduction.png
figB_umap_by_Tw_recovery_time.png
figC_cluster_occupancy_lag_by_cluster.png
figD_cycle_groups_along_PC1.png
figE_presister_like_PCA_UMAP.png
```

Also save vector versions when possible:

```text
.svg or .pdf
```

---

# 5. Recommended priority for tonight's run

For the parameter-search / validation stage, prioritize the figures in this order:

```text
1. Fig. A: RCCN ageing reproduction
2. Fig. E: presister-like vs normal PCA/UMAP
3. Fig. B: UMAP by Tw and recovery time
4. Fig. C left: cluster occupancy vs Tw
5. Fig. C right and Fig. D: auxiliary interpretation
```

Reason:

- Fig. A proves the model implementation is running.
- Fig. E tests the central biological claim most directly.
- Fig. B gives a visually intuitive single-cell state-space story.
- Fig. C quantifies cluster changes.
- Fig. D is mechanistic but depends on whether the model output contains clean cycle-level features.

---

# 6. Short scientific narrative for the figure set

The figure set should support the following story:

```text
First, we reproduce the RCCN model's waiting-time-dependent recovery dynamics. Next, we treat each simulation as a single-cell spin-state trajectory and ask whether starvation duration reshapes the low-dimensional state space. We then quantify whether unsupervised spin-state clusters change their occupancy with Tw and whether those clusters correspond to slow recovery. Finally, using experimentally motivated tail fractions from Kaplan et al. Fig. 2c, we define presister-like simulated cells as the slowest-recovering fraction within each Tw and test whether they occupy a distinct or transitional region in PCA/UMAP space. If successful, this provides a bridge between the generic RCCN spin-glass model and the single-cell persister-state logic of Blattman et al.
```

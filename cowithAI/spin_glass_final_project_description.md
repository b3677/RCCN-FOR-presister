# Final Project Description: Spin-Glass States and Expression-State Heterogeneity in Antibiotic Persistence

## 1. Project Title

**A minimal spin-glass analysis of aging-dependent cell-state heterogeneity in antibiotic persistence**

中文理解：

**用 spin-glass 模型分析抗生素 persistence 中依赖 aging 的细胞状态异质性**

---

## 2. Project Background and Scientific Question

### 2.1 Biological background

Antibiotic persister cells are phenotypic variants that survive otherwise lethal antibiotic treatment without necessarily carrying genetic resistance mutations. A common interpretation is that persisters occupy a slow-growing, dormant, or slow-recovering physiological state. After stress is removed or nutrients become available again, these cells can resume growth only after a long lag phase.

The paper **Observation of universal ageing dynamics in antibiotic persistence** proposes that bacterial persistence after acute stress can be interpreted through an analogy to aging in physical glassy systems. In the experiments, the distribution of recovery or lag times depends on the duration of starvation or acute perturbation. In other words, the longer the system waits under stress, the slower or broader the recovery dynamics become.

The course final project asks students to explore a quantitative principle in biological systems at roughly the scale of a large problem set. The persistence paper is listed as a possible project theme, with the guiding question: what data can be used to test the spin-glass model of persistence?

### 2.2 Instructor feedback and project motivation

The instructor suggested trying to connect the spin states in the model to expression data:

> Cluster both the spin states in model simulations and the data where available, then see if the clusters share some properties. At least within the model, do the spins look different during different stages of aging?

Therefore, the minimal scientific questions for this project are:

1. **Within the RCCN / spin-glass model, do spin states differ across aging stages or waiting times?**
2. **Are spin-state clusters associated with recovery time or lag time?**
3. **Can single-cell expression data from the 2024 PETRI-seq persister atlas provide an empirical comparison for cell-state clustering?**

The goal is not to prove a one-to-one mapping between model spins and genes. Instead, the goal is to test whether both model simulations and expression data support a common quantitative picture:

> Persistence can be viewed as a high-dimensional cell-state problem, where acute stress drives cells into heterogeneous internal states with slow, history-dependent recovery.

---

## 3. Scientific Principle: Spin Glass and Aging

### 3.1 Spin variables

In a spin model, each node has a binary state:

```math
s_i(t) \in \{-1,+1\}
```

In physics, this variable can represent the orientation of a magnetic moment. In the biological analogy used here, each spin represents a coarse-grained internal cellular component or activity state.

A possible interpretation is:

```math
s_i = +1: \text{inactive / OFF}
```

```math
s_i = -1: \text{active / ON}
```

The exact sign convention should follow the original MATLAB implementation of the RCCN model. In the original model, acute stress is represented by an external field that tends to push spins toward the inactive or OFF direction.

### 3.2 General spin-glass energy function

A standard spin-glass model can be written as:

```math
E = -\sum_{ij} J_{ij}s_i s_j
```

where:

- `s_i` and `s_j` are binary spin states;
- `J_ij` is the interaction between spins `i` and `j`;
- `J_ij > 0` favors aligned spins;
- `J_ij < 0` favors anti-aligned spins.

When many constraints in the system are mutually incompatible, the system is **frustrated**. Frustration creates a rugged state space or energy landscape with many metastable states. This is the key physical intuition behind using spin-glass models as simplified models of complex biological dynamics.

In this project, the general spin-glass formula is mainly used for intuition. The specific model to be analyzed is the RCCN model described below.

---

## 4. Scientific Principle: RCCN Model

RCCN stands for:

```text
Randomly Connected Cycles Network
```

It is a toy model designed to capture several abstract features of cellular regulatory networks:

1. The cell contains many interacting internal components.
2. Each component can be coarse-grained into an active or inactive state.
3. The network contains feedback cycles.
4. Acute stress drives the system away from its normal state.
5. After stress removal, the system must recover through a complex high-dimensional state space.

The RCCN model should be implemented as closely as possible to the original MATLAB code and the original paper description.

---

## 5. General Random Spin Dynamics

The supplementary model first introduces a zero-temperature Glauber-like spin update rule:

```math
s_i(t+1)
=
\operatorname{sign}
\left(
\sum_{j\neq i} J_{ij}s_j(t) + H(t) + \xi(t)
\right)
```

where:

- `s_i(t)` is the state of spin `i` at time `t`;
- `J_ij` is the effect of spin `j` on spin `i`;
- `H(t)` is an external field representing acute stress;
- `xi(t)` is short-range correlated external noise;
- `sign(...)` binarizes the input into `-1` or `+1`.

Biological interpretation:

> The next state of each cellular component depends on inputs from other components, the external stress field, and possible noise.

However, the project should focus on the RCCN model rather than a fully connected SK-like spin glass.

---

## 6. RCCN Network Structure

### 6.1 Cycle-length distribution

The RCCN model is composed of many feedback cycles. The length of cycle `i` is denoted by:

```math
L_i
```

Cycle lengths are sampled from a truncated power-law distribution:

```math
P(L) = \nu L^{-\alpha},
\qquad
L_{\min} \le L \le L_{\max}
```

where:

- `L` is cycle length;
- `alpha` is the power-law exponent;
- `nu` is the normalization constant;
- `L_min` and `L_max` are lower and upper bounds for cycle length.

The original model uses typical parameters:

```math
\alpha = 1.5,
\qquad
L_{\min}=1,
\qquad
L_{\max}=2500
```

and a total number of spins approximately:

```math
N = 2^{14}
```

This gives roughly:

```math
N_c \sim 410
```

cycles.

The power-law cycle-length distribution means that the network has no single characteristic feedback timescale. Short and long feedback loops coexist, which can generate broad recovery-time distributions and aging-like dynamics.

---

## 7. RCCN State Variables and Update Rules

### 7.1 Spin notation within cycles

Let:

```math
s_i^{(k)}(t)
```

be the state of the `k`-th node in the `i`-th cycle at time `t`, where:

```math
k = 0,1,2,\dots,L_i-1
```

The node:

```math
s_i^{(0)}(t)
```

is the connection node of cycle `i`. It receives input from other cycles and from its own cycle feedback.

### 7.2 Internal shift dynamics

Inside each cycle, states propagate through the cycle by shift dynamics:

```math
s_i^{(k+1)}(t+1) = s_i^{(k)}(t),
\qquad
1 \le k \le L_i-1
```

This means that a state at one node is passed to the next node in the cycle at the next time step.

Biological intuition:

> Feedback loops create memory and delayed responses. A perturbation can continue to influence the system after the external stress has been removed.

### 7.3 Connection-node update

The connection node of each cycle is updated by combining:

1. feedback from the end of its own cycle;
2. inputs from other cycles;
3. the external stress field.

The update rule is:

```math
s_i^{(0)}(t+1)
=
\operatorname{sign}
\left(
 s_i^{(L_i-1)}(t)
+
\sum_{j\neq i}^{N_c} J_{ij}s_j^{(0)}(t)
+
H(t)
\right)
```

where:

- `N_c` is the number of cycles;
- `J_ij` is the coupling from cycle `j` to cycle `i`;
- `H(t)` is the stress field;
- `s_i^(L_i-1)(t)` is the last node in cycle `i`, which feeds back into the connection node.

This is the core dynamical equation of the RCCN model and should be implemented carefully.

---

## 8. Coupling Between Cycles

The inter-cycle coupling matrix is asymmetric:

```math
J_{ij} \neq J_{ji}
```

This reflects the directed nature of biological regulation: if component A regulates component B, B does not necessarily regulate A in the same way.

The couplings are independent random variables with mean zero and variance scaled by the number of cycles:

```math
\langle J_{ij}^{2} \rangle = \frac{\gamma^2}{N_c}
```

Equivalently:

```math
J_{ij} \sim \mathcal{N}\left(0,\frac{\gamma^2}{N_c}\right)
```

where:

- `gamma` controls the interaction strength between cycles;
- `N_c` is the number of cycles;
- the `1/N_c` scaling prevents the total input from diverging as network size increases.

The original supplementary description notes that when:

```math
\gamma > 1.3
```

weak external noise has little effect, so simulations can set noise to zero.

---

## 9. Stress Protocol

Acute stress is represented by an external field:

```math
H(t)=
\begin{cases}
H_0, & 0 < t \le T_w \\
0, & t > T_w
\end{cases}
```

where:

- `H_0` is the stress strength;
- `T_w` is the waiting time or stress duration;
- larger `T_w` means the system remains under stress for a longer time.

The original model uses a typical value:

```math
H_0 = 0.8
```

During stress, `H(t)` drives the spin system toward an OFF or inactive state. After stress removal, `H(t)=0`, and the system begins to recover.

---

## 10. Magnetization and Lag Time

### 10.1 Cycle-averaged magnetization

The project should strictly use the original RCCN cycle-averaged magnetization, not a simplified all-spin average.

For each cycle, first compute the average spin state within that cycle:

```math
m_i(t)
=
\frac{1}{L_i}
\sum_{k=0}^{L_i-1} s_i^{(k)}(t)
```

Then average across cycles:

```math
M(t)
=
\frac{1}{N_c}
\sum_{i=1}^{N_c} m_i(t)
```

Combining these two equations:

```math
M(t)
=
\frac{1}{N_c}
\sum_{i=1}^{N_c}
\frac{1}{L_i}
\sum_{k=0}^{L_i-1} s_i^{(k)}(t)
```

where:

- `M(t)` is the global magnetization;
- `N_c` is the number of cycles;
- `L_i` is the length of cycle `i`;
- `s_i^(k)(t)` is the spin state of node `k` in cycle `i`.

This definition weights each cycle equally, regardless of the number of spins in the cycle. This is different from the simple all-spin average:

```math
M_{simple}(t)=\frac{1}{N}\sum_{i=1}^{N}s_i(t)
```

The simplified version should **not** be used for reproducing the original RCCN model.

### 10.2 Lag time as first-passage time

Before stress, the system has a baseline magnetization. During stress, magnetization is driven away from baseline. After stress removal, the system recovers.

If the baseline is set to zero, lag time can be defined as the first-passage time after stress removal:

```math
\tau
=
\min
\left\{
t > T_w:
M(t) \le 0
\right\}
-
T_w
```

More generally, if the baseline magnetization is `M_0`, then:

```math
\tau
=
\min
\left\{
t > T_w:
M(t) \le M_0
\right\}
-
T_w
```

where:

- `T_w` is the waiting time or stress duration;
- `tau` is the recovery time after stress removal;
- `tau` corresponds to the biological lag time or recovery time.

This first-passage-time definition is central to the project because later analysis will test whether different spin-state clusters correspond to different `tau` distributions.

---

## 11. Aging Dynamics and Recovery-Time Distributions

For each waiting time `T_w`, many simulated cells are generated. Each simulation produces a recovery time:

```math
\tau_n(T_w)
```

where `n` indexes simulated cells.

The empirical cumulative distribution function is:

```math
\hat{F}_{T_w}(t)
=
\frac{1}{N_{cells}}
\sum_{n=1}^{N_{cells}}
\mathbf{1}
\left[
\tau_n(T_w) \le t
\right]
```

The complementary distribution is:

```math
1-\hat{F}_{T_w}(t)
```

This quantity represents the fraction of cells that have not yet recovered by time `t` after stress removal.

Aging-like dynamics are present if increasing `T_w` changes the recovery-time distribution, typically by shifting it to longer times or broadening its tail:

```math
T_w \uparrow
\quad \Rightarrow \quad
\tau \text{ distribution becomes longer and/or broader}
```

This recovery-time distribution should be used as a benchmark when translating or rebuilding the model in Python.

---

## 12. Spin-State Matrix for Clustering

The key new analysis in this project is to save spin states from the RCCN simulations.

For each simulated cell `n`, save a spin-state vector at a selected time point `t*`:

```math
\mathbf{s}_n(t^*)
=
\left[
s_{n,1}(t^*),
s_{n,2}(t^*),
\dots,
s_{n,N}(t^*)
\right]
```

This gives a matrix:

```math
X_{spin}
\in
\mathbb{R}^{N_{cells}\times N_{spins}}
```

where:

- rows are simulated cells or simulation replicates;
- columns are spin variables;
- entries are binary values, usually `-1` or `+1`.

Recommended snapshots:

1. **Release state**:

```math
\mathbf{s}_n(T_w)
```

This is the spin configuration at the moment stress is removed.

2. **Early recovery state**:

```math
\mathbf{s}_n(T_w+\Delta t)
```

This is the spin configuration shortly after stress removal.

The release state is the minimal required snapshot. The early recovery state is optional.

---

## 13. PCA and Clustering of Spin States

### 13.1 PCA

Given the spin-state matrix `X_spin`, first center each spin dimension:

```math
\tilde{X}_{ij}
=
X_{ij}
-
\bar{X}_{\cdot j}
```

The covariance matrix is:

```math
C
=
\frac{1}{N_{cells}-1}
\tilde{X}^{T}\tilde{X}
```

Principal components are obtained by solving:

```math
C\mathbf{v}_k
=
\lambda_k\mathbf{v}_k
```

The score of cell `n` on principal component `k` is:

```math
z_{nk}
=
\tilde{\mathbf{x}}_n \cdot \mathbf{v}_k
```

PCA is used to visualize whether spin states sampled at different waiting times separate, drift, or broaden in a low-dimensional state space.

### 13.2 k-means clustering

After PCA or another dimensionality-reduction step, k-means can be applied to the low-dimensional representation:

```math
\min_{\{C_k\}}
\sum_{k=1}^{K}
\sum_{n\in C_k}
\left\|
\mathbf{z}_n - \boldsymbol{\mu}_k
\right\|^2
```

where:

```math
\boldsymbol{\mu}_k
=
\frac{1}{|C_k|}
\sum_{n\in C_k}
\mathbf{z}_n
```

The goal is not to over-interpret k-means clusters. The goal is to test whether clusters are associated with waiting time and recovery time.

### 13.3 Cluster occupancy

For each waiting time `T_w`, compute the fraction of simulations in cluster `k`:

```math
p_k(T_w)
=
\frac{
\#\{n: c_n=k,\; T_{w,n}=T_w\}
}{
\#\{n: T_{w,n}=T_w\}
}
```

If some clusters become enriched as `T_w` increases, this suggests that aging changes the internal state distribution of the model.

### 13.4 Cluster-specific lag-time distribution

For each cluster, compute the distribution:

```math
P(\tau \mid c=k)
```

and the mean recovery time:

```math
\bar{\tau}_k
=
\frac{1}{N_k}
\sum_{n:c_n=k}
\tau_n
```

If some clusters have longer mean recovery time, they can be interpreted as slow-recovering or persister-like internal states in the model.

---

## 14. Connection to 2024 PETRI-seq Persister Atlas

### 14.1 Relevant expression data

The most relevant expression dataset for comparison is the 2024 paper:

**Identification and genetic dissection of convergent persister cell states**

This paper generated a high-resolution single-cell RNA atlas of *E. coli* growth transitions using PETRI-seq. It identified a distinct persister cell state that appears across multiple genetic and physiological models of persistence, including metG*, hipA7, 6-day wild-type starvation, and tetracycline-treated cells.

The key biological message of that paper is that persister cells from different models converge to related transcriptional states. These persister states are distinct from standard stationary, lag, and exponential growth phases, and are primarily associated with translational deficiency.

### 14.2 Expression-state matrix

The expression data can be represented as:

```math
X_{expr}
\in
\mathbb{R}^{N_{cells}\times N_{genes}}
```

where:

- rows are single cells;
- columns are genes;
- entries are UMI counts or normalized expression values.

The 2024 paper processed the PETRI-seq data using a Seurat-based workflow, including filtering, downsampling, normalization, PCA, UMAP, and Louvain clustering.

For this project, the expression-data analysis strategy is **not fixed yet**. The likely plan is to use processed data or published cluster annotations rather than reprocess raw sequencing data.

### 14.3 Weak correspondence between model and data

The model should not be interpreted as assigning each spin to a specific gene. A safer interpretation is a weak state-space correspondence:

| RCCN / spin model | PETRI-seq expression atlas |
|---|---|
| spin vector `s_n` | expression vector `x_n` |
| waiting time `T_w` | starvation duration or experimental condition |
| magnetization `M(t)` | global cell-state axis |
| first-passage time `tau` | lag time / recovery delay |
| spin-state cluster | transcriptional cell-state cluster |
| slow-recovering spin cluster | persister-like transcriptional cluster |
| frustrated network recovery | translationally deficient or dysregulated recovery state |

The intended interpretation is:

> The RCCN model does not directly predict gene expression. Instead, it predicts that acute stress can push cells into heterogeneous high-dimensional internal states whose recovery time depends on waiting time. The PETRI-seq atlas provides an empirical single-cell state space in which persister-like cells also appear as distinct or enriched clusters.

---

## 15. Approximate Project Tasks

The engineering plan is intentionally kept high-level at this stage.

### Task A. Reproduce the core RCCN model behavior

Use the original MATLAB code or a minimal Python reimplementation to reproduce the qualitative aging behavior of the RCCN model.

Expected output:

- recovery-time or lag-time distributions for multiple waiting times `T_w`;
- confirmation that longer waiting times produce aging-like changes in recovery dynamics.

### Task B. Save spin-state snapshots

Modify or reimplement the simulation so that it saves spin states at key time points:

```math
\mathbf{s}_n(T_w)
```

and optionally:

```math
\mathbf{s}_n(T_w+\Delta t)
```

Also save metadata:

```text
simulation_id
waiting_time
lag_time
snapshot_time
model_parameters
```

### Task C. Cluster spin states

Use PCA, UMAP, k-means, or hierarchical clustering to analyze the spin-state matrix.

Minimal outputs:

1. PCA/UMAP colored by waiting time;
2. PCA/UMAP colored by cluster;
3. cluster occupancy as a function of waiting time;
4. lag-time distribution by cluster.

### Task D. Examine the 2024 PETRI-seq data

This step is pending and will be decided later. The likely strategy is to use processed data, source data, or published cluster annotations rather than raw PETRI-seq reads.

Possible checks:

- whether processed cell-by-gene matrices are available;
- whether cell metadata and cluster labels are available;
- whether published UMAP/PCA coordinates can be reused;
- whether persister-cluster occupancy across conditions can be reproduced or summarized.

### Task E. Compare model clusters and expression clusters

This step is also pending. The comparison should remain qualitative or semi-quantitative unless the processed data are easy to use.

Possible outputs:

- a simplified expression-state UMAP or PCA;
- a bar plot of persister-cluster enrichment across conditions;
- a conceptual comparison between model slow-recovery clusters and expression persister clusters.

### Task F. Build final project figures

The final report likely needs 3-4 main figures:

1. RCCN model schematic and biological interpretation;
2. model recovery-time distribution showing aging;
3. spin-state clustering and cluster occupancy versus waiting time;
4. expression-data comparison using the 2024 PETRI-seq persister atlas.

---

## 16. Minimal Success Criteria

The project is successful if it achieves the following:

1. Different waiting times in the RCCN model generate spin states that can be saved and analyzed.
2. Spin states can be visualized or clustered in a low-dimensional state space.
3. Spin-state clusters show some relationship with waiting time or recovery time.
4. The 2024 PETRI-seq persister atlas is used as a biological reference showing that real persister cells also occupy distinct or enriched expression states.
5. The final interpretation is framed carefully: the model and data support a shared high-dimensional state-space view of persistence, not a direct gene-by-spin mapping.

---

## 17. Notes for Python Reimplementation

If the MATLAB RCCN code is translated into Python, the translation should be minimal and validation-driven.

Do not rewrite the full repository at once. Instead:

1. Identify the MATLAB main simulation script.
2. Identify the parameter definitions.
3. Identify the cycle construction logic.
4. Identify the spin update rule.
5. Identify the magnetization calculation.
6. Identify the lag-time / first-passage-time definition.
7. Reimplement only the minimal simulation core in Python.
8. Validate the Python output against the original MATLAB behavior.

Important implementation cautions:

- MATLAB uses 1-based indexing; Python uses 0-based indexing.
- The cycle-averaged magnetization must be preserved.
- Synchronous versus asynchronous update rules must match the original code.
- The sign convention must match the original code.
- The lag-time threshold must match the original code.
- Random seeds do not need to produce identical trajectories, but statistical outputs should match qualitatively.

Recommended validation levels:

1. **Toy deterministic test**: small network, fixed coupling matrix, fixed initial state, compare one-step or few-step updates.
2. **Parameter check**: confirm `N`, `N_c`, `alpha`, `L_min`, `L_max`, `gamma`, `H_0`, and `T_w` values.
3. **Statistical benchmark**: compare recovery-time distributions across waiting times with the original model.

---

## 18. Working Summary

This project will use the RCCN spin-glass model as a minimal quantitative model of bacterial persistence and aging. The key model prediction to test is that acute stress drives cells into heterogeneous internal spin states, and that these states change with waiting time and influence recovery time. The computational core will save and cluster spin-state snapshots from simulations. The biological comparison will use the 2024 PETRI-seq persister atlas as an empirical example of high-dimensional single-cell state heterogeneity in persistence.

The final interpretation should be cautious but clear:

> The RCCN model provides a physical picture of persistence as slow recovery in a frustrated high-dimensional cellular state space. Single-cell expression data provide a biological state-space view in which persisters also appear as distinct or enriched transcriptional states. The project tests whether these two views can be connected at the level of cell-state heterogeneity, clustering, and recovery dynamics.

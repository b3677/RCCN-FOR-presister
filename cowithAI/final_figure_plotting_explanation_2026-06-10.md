# RCCN 最终图 A-E 绘图说明与计算来源

本文档整合当前最终绘图代码、现有输出数据和 `final_figure_revision_requests_2026-06-10.md` 中的修改要求。目标是让每张图的科学目的、图中每个量的含义、计算函数来源和当前待修改点都可追踪。

## 1. 当前最终绘图流水线

当前最终图 A-E 的入口是：

```text
scripts/make_final_project_figures.py
```

它读取：

```text
output/final_analysis/
```

并保存图片到：

```text
output/final_figures/
```

当前已经存在的最终图文件：

```text
figA_rccn_ageing_reproduction.png
figB_umap_by_Tw_recovery_time.png
figC_cluster_occupancy_lag_by_cluster.png
figD_cycle_groups_along_PC1.png
figE_presister_like_PCA_UMAP.png
```

当前全量 pipeline 已在 2026-06-10 跑完：

```text
full_final_simulation: exit_code=0
full_final_analysis: exit_code=0
full_final_figures: exit_code=0
```

现有最终模拟参数：

```text
Tw = 0, 195, 488, 1346, 1500 min
n_runs = 900 per Tw
selected_recovery_times = 0, 20, 120 min
num_spins = 16384
pca_components = 10
n_clusters = 3
```

## 2. 主要数据表和矩阵

### `output/final_simulation/metadata.csv`

一行代表一个 simulated cell / trajectory。当前有：

```text
4500 rows = 5 Tw values * 900 runs
```

关键列：

| 列名 | 含义 | 计算来源 |
|---|---|---|
| `run_id` | 单个模拟细胞 / trajectory 的编号 | `simulation.run_batch()` |
| `Tw` | stress / waiting time | `config.make_final_project_params()` |
| `recovery_time` | 当前代码定义的 lag / recovery time | `observables.compute_recovery_time()` |
| `recovered` | 是否在 relax window 内恢复 | `observables.compute_recovery_time()` |
| `baseline_magnetization` | stress 前 baseline magnetization | `observables.compute_baseline_magnetization()` |
| `snapshot_time` | release 时刻，等于 `init_time + Tw` | `simulation.run_one_cell()` |
| `early_recovery_snapshot_time` | release 后 early snapshot 时刻 | `simulation.run_one_cell()` |
| `num_cycles` | 该 cell 的 RCCN cycle 数量 | `network.build_rccn_network()` |

重要说明：当前 `recovery_time` 不是修订要求里“`M` 回到 `0`”的 paper-style lag time。当前代码使用的是：

```text
stress release 后第一次满足 magnetization < baseline_magnetization 的时间
```

### `output/final_simulation/magnetization.csv`

长表，每行是一个 `run_id` 在一个 simulation time 的 global magnetization。

关键列：

| 列名 | 含义 | 计算来源 |
|---|---|---|
| `run_id` | simulated cell 编号 | `simulation.run_one_cell()` |
| `Tw` | waiting time | `simulation.run_one_cell()` |
| `time` | simulation absolute time | `dynamics.run_one_protocol()` |
| `magnetization` | cycle-averaged global magnetization | `observables.compute_global_magnetization()` |

`magnetization` 的计算是：

```text
1. 对每个 cycle 求 mean spin
2. 再对所有 cycles 求平均
```

对应函数：

```text
observables.compute_cycle_magnetization()
observables.compute_global_magnetization()
```

### `output/final_simulation/selected_spin_snapshots.npy`

高维 spin-state feature matrix。当前形状：

```text
(13500, 16384)
```

含义：

```text
13500 rows = 4500 cells * 3 recovery snapshots
16384 columns = RCCN spins
```

行身份由 `snapshot_metadata.csv` 对齐。

### `output/final_simulation/snapshot_metadata.csv`

一行对应 `selected_spin_snapshots.npy` 的一行。

关键列：

| 列名 | 含义 |
|---|---|
| `run_id` | simulated cell 编号 |
| `Tw` | waiting time |
| `state_recovery_time` | release 后采样状态时间，当前为 `0`, `20`, `120` |
| `absolute_snapshot_time` | simulation absolute time |

### `output/final_analysis/cell_state_table.csv`

最终 A-E 里 B/C/E/D 的核心表。当前有：

```text
13500 rows = 4500 cells * 3 sampled states
```

关键列：

| 列名 | 含义 | 计算来源 |
|---|---|---|
| `simulation_id`, `run_id` | simulated cell identity | `spin_analysis.build_cell_state_table()` |
| `Tw` | waiting time | 来自 `snapshot_metadata.csv` |
| `state_recovery_time` | spin state snapshot 相对 release 的时间 | `simulation.run_one_cell()` |
| `recovery_time`, `lag_time` | 当前代码的 recovery time / lag time | `observables.compute_recovery_time()` |
| `recovered_label` | 是否恢复 | `observables.compute_recovery_time()` |
| `cluster_id` | unsupervised spin-state cluster | `spin_analysis.run_clustering()` |
| `presister_like` | 是否属于 tail-fraction-defined slowest group | `observables.assign_presister_like_by_tail_fraction()` |
| `state_label` | `normal` 或 `presister-like` | `observables.assign_presister_like_by_tail_fraction()` |
| `PC1`, `PC2`, ..., `PC10` | PCA score | `spin_analysis.run_pca()` |
| `UMAP1`, `UMAP2` | UMAP coordinate | `spin_analysis.run_umap()` |

### `output/final_analysis/tail_fraction_by_Tw.csv`

来自 `data/sourcefig2.xlsx` 的 Fig. 2c tail fraction 数据，供 Fig. B 注释和 Fig. E presister-like 定义使用。

关键列：

| 列名 | 含义 | 计算来源 |
|---|---|---|
| `Tw` | waiting time | `observables.load_tail_fraction_table()` |
| `TailFraction` | 该 `Tw` 下最慢恢复细胞比例 | `observables.load_tail_fraction_table()` |
| `TailFractionSTD` | source data 中的不确定度 | `observables.load_tail_fraction_table()` |
| `TailFraction_source` | direct 或 extrapolated | `observables.load_tail_fraction_table()` |

### `output/final_analysis/cluster_summary_by_Tw.csv`

Fig. C 左图使用的 cluster composition 表。

关键列：

| 列名 | 含义 | 计算来源 |
|---|---|---|
| `Tw` | waiting time | `observables.summarize_cluster_by_Tw()` |
| `cluster_id` | spin-state cluster | `spin_analysis.run_clustering()` |
| `n_cells` | 该 `Tw` / cluster 中的 cell 数 | `observables.summarize_cluster_by_Tw()` |
| `cluster_fraction` | 该 cluster 在该 `Tw` 的比例 | `observables.summarize_cluster_by_Tw()` |
| `mean_lag_time` | 该组平均 lag time | `observables.summarize_cluster_by_Tw()` |
| `median_lag_time` | 该组中位 lag time | `observables.summarize_cluster_by_Tw()` |
| `presister_like_fraction` | 该 cluster 中 presister-like 比例 | `observables.summarize_cluster_by_Tw()` |

### `output/final_analysis/cycle_pc1_moving_average.csv`

当前 Fig. D 使用的混合所有 `Tw` 的 PC1 moving-average 表。

关键列：

| 列名 | 含义 | 计算来源 |
|---|---|---|
| `PC1_window_center` | 按 PC1 排序后的滑窗中心 | `spin_analysis.compute_cycle_pc1_moving_average()` |
| `cycle_group` | `short`, `medium`, `long` cycle group | `observables.compute_cycle_group_features()` |
| `mean_cycle_activation` | 窗口内该 cycle group 的平均 magnetization | `spin_analysis.compute_cycle_pc1_moving_average()` |
| `sem_cycle_activation` | 窗口内该均值的 SEM | `spin_analysis.compute_cycle_pc1_moving_average()` |
| `n_cells_in_window` | 每个滑窗中的 cell 数 | `spin_analysis.compute_cycle_pc1_moving_average()` |
| `window_size` | moving average window size，当前为 100 | `spin_analysis.compute_cycle_pc1_moving_average()` |

注意：当前这个表没有 `Tw` 列，所以它只能直接画 mixed-all-`Tw` 版本。要画每个 `Tw` 单独版本，需要从已有 `cell_state_table.csv` 和 `cycle_group_features.csv` 重新计算 per-`Tw` moving average。

## 3. Fig. A: RCCN ageing / recovery survival

### 当前代码状态

当前入口：

```text
plotting.plot_figA_recovery_dynamics()
```

当前输入：

```text
output/final_analysis/recovery_dynamics_by_Tw.csv
```

当前 y 轴：

```text
Mean cycle-averaged magnetization
```

当前计算来源：

```text
observables.compute_recovery_dynamics_by_Tw()
```

该函数把 `magnetization.csv` 和 `metadata.csv` 合并，用：

```text
recovery_time = time - snapshot_time
```

然后对每个 `Tw` 和 `recovery_time` 求：

```text
mean_recovery_observable = mean(magnetization)
std_recovery_observable
sem_recovery_observable
n_simulations
```

### 修订后应画的量

修订要求：

```text
y-axis = 1 - CDF = fraction of cells not yet resumed growth
```

paper-style lag-time definition：

```text
lag time = time when magnetization M returns to 0
cells with M = 0 are treated as recovered / resumed-growth cells
```

因此修订后的 Fig. A 不应再用 mean magnetization 作为 y 轴，而应使用每个 `Tw` 下随 recovery time 变化的未恢复比例：

```text
S(t | Tw) = fraction of cells whose first M-return-to-0 time is greater than t
```

等价于：

```text
S(t | Tw) = 1 - CDF(t | Tw)
```

### 图中每个量的含义

| 图中元素 | 含义 |
|---|---|
| x-axis: recovery time after nutrient restoration | release 后经过的 simulation step，按 1 step ≈ 1 min 显示 |
| y-axis: `1 - CDF` | 到该 recovery time 仍未恢复 / 未 resumed growth 的细胞比例 |
| one curve per `Tw` | 不同 stress / waiting time 下的恢复尾部分布 |
| semi-log subplot | y 轴 log，突出长尾恢复 |
| log-log subplot | x 和 y 都 log，检查尾部是否近似 power-law / broad distribution |

### 科学目的

Fig. A 是模型验证图。它回答：

```text
当前 Python RCCN 模拟是否能复现 waiting-time-dependent ageing：
Tw 越长，恢复分布越慢 / 尾部越重？
```

### 当前差距

1. 当前 Fig. A 画的是 mean magnetization，不是 `1 - CDF`。
2. 当前 `metadata.recovery_time` 使用 baseline-crossing 定义，不是 `M = 0` 定义。
3. 需要新增或修改计算函数，从 `magnetization.csv` 直接计算 paper-style recovery time，再得到 survival curve。

## 4. Fig. B: UMAP by Tw and recovery snapshot time

### 当前代码状态

当前入口：

```text
plotting.plot_figB_umap_by_Tw_recovery_time()
```

当前输入：

```text
cell_state_table.csv
tail_fraction_by_Tw.csv
```

当前面板：

```text
Tw = 0, 488, 1346
```

当前 recovery snapshot colors：

```text
0 min   -> #4C78A8
20 min  -> #59A14F
120 min -> #E15759
```

当前 UMAP 坐标计算来源：

```text
spin_analysis.run_pca()
spin_analysis.run_umap()
```

当前 UMAP 输入是 selected spin snapshots 的 PCA score：

```text
selected_spin_snapshots.npy
    -> run_pca()
    -> first PCs
    -> run_umap()
```

### 图中每个量的含义

| 图中元素 | 含义 |
|---|---|
| each panel | 一个 selected `Tw` 下的 simulated cell states |
| each point | 一个 simulated cell 在一个 sampled recovery time 的 spin-state snapshot |
| x-axis: `UMAP1` | 高维 spin-state feature 的 UMAP 第 1 坐标 |
| y-axis: `UMAP2` | 高维 spin-state feature 的 UMAP 第 2 坐标 |
| color | release 后采样时间：0, 20, 120 min |
| tail fraction text | 该 `Tw` 下 source Fig. 2c 的 slow-recovery tail fraction |

### 修订要求

颜色改为：

```text
0 min   -> RGB(255, 183, 3)
20 min  -> RGB(90, 24, 154)
120 min -> RGB(230, 57, 20)
```

新增 auxiliary trajectory summary：

```text
对每个 Tw panel 和每个 recovery snapshot time：
    1. 在 UMAP 空间中计算该 time 的 centroid
    2. 按 0 -> 20 -> 120 min 顺序用箭头连接 centroid
```

### 科学目的

Fig. B 询问：

```text
RCCN simulated cells 在恢复过程中是否沿低维状态空间发生系统性位移？
长 Tw 是否产生更明显的状态滞留、分支或 slow-recovery 区域？
```

centroid 箭头只应解释为平均状态空间位移的视觉辅助，不应替代单细胞散点。

### 当前差距

1. 颜色需要替换。
2. 需要在当前 scatter 上叠加 centroid arrows。
3. 当前数据已经有 `state_recovery_time = 0, 20, 120`，无需重跑模拟。

## 5. Fig. C: cluster occupancy and lag distribution

### 当前代码状态

当前入口：

```text
plotting.plot_figC_cluster_occupancy_and_lag()
```

当前输入：

```text
cluster_summary_by_Tw.csv
cell_state_table.csv
```

当前左图：

```text
stacked bar plot:
x = Tw
y = cluster_fraction
color = cluster_id
```

当前右图：

```text
violin plot + median + jittered points:
x = cluster_id
y = lag_time
```

### 三个 spin clusters 如何定义

当前 cluster 定义是无监督的：

```text
1. 从 selected_spin_snapshots.npy 取 spin-state feature matrix
2. 对 spin features 做 centering + PCA
3. 使用前 10 个 PC score 作为低维表示
4. 用 sklearn KMeans(n_clusters=3, random_state=1, n_init=20) 聚类
5. 得到每一行 feature_row_id 的 cluster_id
```

对应函数：

```text
spin_analysis.build_spin_feature_matrix()
spin_analysis.run_pca()
spin_analysis.run_clustering()
spin_analysis.build_cell_state_table()
```

重要解释：

```text
cluster_id 是 KMeans 的编号，不天然有 biological order。
需要通过 cluster_fraction, median_lag_time, presister_like_fraction, mean_PC1 等后验量解释哪个 cluster 更 slow-recovery / persister-like。
```

### 右图如何读

当前右图不是三个单点，也不是 95% quantile 图。它是：

```text
每个 cluster 的 lag_time distribution
```

具体包括：

```text
violin body: 该 cluster 内所有 selected state rows 对应 cell 的 lag_time 分布形状
median line: violinplot(showmedians=True) 显示中位数
jittered dots: 单个 cell 的 lag_time
```

当前 `state_recovery_time_for_cluster_summary = 0`，所以该图默认用 release snapshot 的 cluster assignment 来比较 lag time。

### 图中每个量的含义

| 图中元素 | 含义 |
|---|---|
| left x-axis: `Tw` | stress / waiting time |
| left y-axis: `cluster_fraction` | 该 `Tw` 下属于某 cluster 的 cell 比例 |
| left color | `cluster_id` |
| right x-axis: `cluster_id` | spin-state cluster |
| right y-axis: `lag_time` | 当前代码的 recovery time / lag time |
| jittered points | 单个 simulated cell 的 lag_time |
| violin shape | cluster 内 lag_time 分布 |

### 修订要求

cluster colors 改为：

```text
cluster 0 -> RGB(65, 152, 172)
cluster 1 -> RGB(123, 192, 205)
cluster 2 -> RGB(219, 203, 146)
```

左图 legend 尽量移到 plotting area 外。

### 科学目的

Fig. C 把状态空间聚类和 ageing phenotype 连接起来：

```text
1. 哪些 spin-state clusters 随 Tw 增加而改变占比？
2. 占比改变的 cluster 是否对应更长 lag / slower recovery？
```

### 当前差距

1. 需要替换 cluster colors。
2. 需要明确 caption / 文档中说明 cluster 是 KMeans on PCA scores。
3. 需要在图注中说明右图是 distribution，不是 95% quantile 或三个 summary points。

## 6. Fig. D: cycle groups along PC1

### 当前代码状态

当前入口：

```text
plotting.plot_figD_cycle_groups_along_PC1()
```

当前输入：

```text
cycle_pc1_moving_average.csv
cell_state_table.csv
```

当前 top panel：

```text
histogram of PC1
```

当前 bottom panel：

```text
x = PC1_window_center
y = mean_cycle_activation
color = short / medium / long cycle group
```

当前计算来源：

```text
observables.compute_cycle_group_features()
spin_analysis.compute_cycle_pc1_moving_average()
```

### y 轴如何计算

第一步，对一个 cell 的一个 spin snapshot，先计算每个 cycle 的 magnetization：

```text
cycle_magnetization = sum(spins in cycle) / cycle_length
```

对应函数：

```text
observables.compute_cycle_magnetization()
```

第二步，在该 cell 自己的 RCCN network 内，按 cycle length 的三分位数把 cycles 分成：

```text
short cycles
medium cycles
long cycles
```

第三步，对每个 cycle group 求平均：

```text
short_cycle_activation  = mean(cycle_magnetization of short cycles)
medium_cycle_activation = mean(cycle_magnetization of medium cycles)
long_cycle_activation   = mean(cycle_magnetization of long cycles)
```

第四步，把 cells 按 PC1 排序，在 sliding window 中计算：

```text
mean_cycle_activation = mean(group_cycle_activation across cells in the window)
```

因此 Fig. D 的 y 轴是：

```text
absolute mean cycle magnetization / activation
```

不是：

```text
relative proportion
```

重要解释：

```text
如果 short loops 的值更小，这不一定表示 short loops 在相对意义上被 depletion。
它可能只是该组 cycle magnetization 的绝对值更低。
```

### 当前 Fig. D 使用的 subset

当前参数：

```text
state_recovery_time_for_figD = 0
```

所以 Fig. D 使用 release-time spin state。

当前 `cycle_pc1_moving_average.csv` 是 mixed-all-`Tw` 版本：

```text
所有 Tw 的 release-state rows 混在一起，按 PC1 排序后做 moving average
```

### 图中每个量的含义

| 图中元素 | 含义 |
|---|---|
| top x-axis: `PC1` | release-state spin features 的第一主成分 |
| top y-axis: cell count | 各 PC1 区间内的 cell 数 |
| bottom x-axis: `PC1_window_center` | PC1 排序后 sliding window 的中心 |
| bottom y-axis: `mean_cycle_activation` | window 内 short/medium/long cycle group 的绝对平均 magnetization |
| color | cycle length group |
| shaded band | `sem_cycle_activation` |

### 修订要求

保留当前 mixed-all-`Tw` 版本，同时额外生成：

```text
Tw = 0
Tw = 195
Tw = 488
Tw = 1346
Tw = 1500
```

每个 `Tw` 一张同格式 Fig. D。所有版本使用相同 y-axis definition 和 cycle-group colors。

### 科学目的

Fig. D 是机制解释图。它问：

```text
沿主要 cell-state axis PC1，RCCN 网络中 short / medium / long feedback cycles 的平均 magnetization 是否呈现不同趋势？
```

注意：由于当前每个 simulated cell 使用独立随机 RCCN network，具体 cycle id 不能跨细胞比较。因此 Fig. D 解释的是：

```text
cycle-length group-level activation
```

不是某个固定 pathway / fixed cycle 的活性。

### 当前差距

1. 当前只有 mixed-all-`Tw` 的 `cycle_pc1_moving_average.csv`。
2. per-`Tw` 图不需要重跑模拟，但需要从现有 `cell_state_table.csv` 和 `cycle_group_features.csv` 重新计算 per-`Tw` moving average。
3. 需要在图注中明确 y 轴是 absolute magnetization，不是 relative proportion。

## 7. Fig. E: presister-like vs normal in PCA and UMAP

### 当前代码状态

当前入口：

```text
plotting.plot_figE_presister_like_pca_umap()
```

当前输入：

```text
cell_state_table.csv
```

当前 subset：

```text
state_recovery_time_for_figE = 0
```

当前 panels：

```text
left: PC1 vs PC2
right: UMAP1 vs UMAP2
```

当前 colors：

```text
normal          -> #4C78A8
presister-like  -> #E15759
```

### presister-like 如何定义

对应函数：

```text
observables.assign_presister_like_by_tail_fraction()
```

定义方式：

```text
对每个 Tw 单独排序：
    recovery_time 最大 / 未恢复的 cells 排在最慢恢复端
    取最慢恢复的 ceil(n_cells * TailFraction) 个 cells
    标记为 presister-like
其余标记为 normal
```

`TailFraction` 来自：

```text
observables.load_tail_fraction_table()
data/sourcefig2.xlsx
```

### RCCN PCA 和 UMAP 中不同 cells 的区别是什么

每个点代表一个 simulated cell 的 high-dimensional spin-state snapshot。

不同点之间的差异来自：

```text
1. 随机 RCCN network
2. 随机 initial spin state
3. stress waiting time Tw
4. recovery snapshot time
5. spin dynamics 后形成的 16384-dimensional spin vector
```

PCA/UMAP 不是用基因表达，而是用 RCCN spin-state features。它们表达的是模型内部状态空间，而不是真实 single-cell transcriptome。

### 图中每个量的含义

| 图中元素 | 含义 |
|---|---|
| each point | 一个 simulated cell 的 release-state spin snapshot |
| PC1/PC2 | spin-state feature 的 PCA 坐标 |
| UMAP1/UMAP2 | spin-state feature 的 UMAP 坐标 |
| color: normal | 不在该 `Tw` 的 slowest TailFraction 内 |
| color: presister-like | 该 `Tw` 下最慢恢复 TailFraction cells |

### 修订要求

颜色改为：

```text
normal         -> RGB(22, 50, 115)
presister-like -> RGB(250, 81, 124)
```

PCA panel 增加 marginal distributions：

```text
PC1 marginal distribution by state_label
PC2 marginal distribution by state_label
```

并保持 marginal distribution colors 和 PCA scatter colors 一致。

### 关于 weak separation 的解释

如果 Fig. E 中 normal 与 presister-like 分离较弱，可能原因包括：

```text
1. RCCN spin features 是抽象模型状态，不是高维 gene-expression phenotype。
2. 当前 presister-like label 来自 recovery-time tail fraction，而不是直接从 PCA/UMAP 聚类定义。
3. tail fraction 很小，presister-like cells 是 rare group，视觉上容易被 normal points 淹没。
4. 如果可区分维度主要不在 PC1/PC2 或 UMAP 的前两个可视化维度，二维图会弱化分离。
5. RCCN 模型可能产生连续 ageing landscape，而不是清楚分开的离散 islands。
```

因此 weak separation 不一定是失败。更谨慎的表述是：

```text
RCCN feature representation may contain lower or more continuous separability than single-cell expression data.
```

### 科学目的

Fig. E 是最直接的 biological bridge 图。它问：

```text
如果不用 clustering，而用外部 tail fraction 定义 slowest-recovering presister-like cells，
这些 cells 是否在 RCCN state space 中富集到某个区域？
```

### 当前差距

1. 颜色需要替换。
2. PCA panel 需要增加 PC1/PC2 marginal distributions。
3. caption 需要说明 presister-like 是 tail-fraction-defined，而不是 KMeans cluster-defined。

## 8. 推荐图注中必须交代的共通事项

1. 时间单位：

```text
1 simulation step is displayed as approximately 1 min.
```

2. 每个点：

```text
Each point represents one simulated RCCN cell / trajectory state.
```

3. recovery / lag time：

```text
Current metadata lag_time uses baseline-crossing recovery time unless Fig. A is explicitly recomputed with the M=0 paper-style definition.
```

4. cluster：

```text
Spin clusters are KMeans clusters on PCA scores of selected spin-state snapshots.
Cluster IDs are arbitrary and interpreted post hoc by occupancy and lag-time summaries.
```

5. presister-like：

```text
Presister-like cells are defined within each Tw as the slowest-recovering TailFraction fraction, using source Fig. 2c-derived tail fractions.
```

6. Fig. D y-axis：

```text
Cycle-group activation is absolute mean cycle magnetization, not a relative proportion.
```


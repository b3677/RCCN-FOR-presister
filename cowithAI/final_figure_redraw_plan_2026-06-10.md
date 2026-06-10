# RCCN 最终图 A-E 重新绘制可行性检查与计划

本文档基于当前代码和 `output/final_*` 现有数据，回答两个问题：

1. 哪些图现在可以利用现有数据重新绘制？
2. 应该按什么顺序修改计算 / 绘图代码并重画？

## 1. 当前数据可用性结论

当前全量输出已经存在：

```text
output/final_simulation/
output/final_analysis/
output/final_figures/
```

核心数据规模：

```text
metadata.csv: 4500 rows
snapshot_metadata.csv: 13500 rows
cell_state_table.csv: 13500 rows
selected_spin_snapshots.npy: (13500, 16384)
spin_release.npy: (4500, 16384)
spin_early_recovery.npy: (4500, 16384)
```

最终图 A-E 的数据基础基本齐全。除非想改变 simulation 参数、重新定义 spin feature 或重新跑 UMAP / KMeans，否则不需要重跑 900 simulations per Tw 的全量模拟。

## 2. 哪些图可以马上用现有数据重新绘制？

| Figure | 是否可用现有数据重画 | 是否需要重跑模拟 | 是否需要重跑 analysis | 主要原因 |
|---|---:|---:|---:|---|
| Fig. A | 可以 | 不需要 | 需要新增/重算 Fig. A survival table | `magnetization.csv` 已有完整时间序列，可从中按 `M=0` 定义重新计算 `1-CDF` |
| Fig. B | 可以 | 不需要 | 不需要 | `cell_state_table.csv` 已有 `UMAP1/UMAP2` 和 `state_recovery_time = 0,20,120` |
| Fig. C | 可以 | 不需要 | 不需要 | `cluster_summary_by_Tw.csv` 和 `cell_state_table.csv` 已有 cluster fraction 和 lag distribution |
| Fig. D mixed all-`Tw` | 可以 | 不需要 | 不需要 | `cycle_pc1_moving_average.csv` 已有 mixed version |
| Fig. D per-`Tw` | 可以 | 不需要 | 需要从现有表重算 per-`Tw` moving averages | 现有 `cycle_pc1_moving_average.csv` 没有 `Tw` 列，但原始 `cell_state_table.csv` 和 `cycle_group_features.csv` 有 `Tw` |
| Fig. E | 可以 | 不需要 | 不需要 | `cell_state_table.csv` 已有 PCA/UMAP 和 `state_label` |

结论：

```text
所有 A-E 都可以利用现有数据重画。
没有一张图必须重跑 simulation。
Fig. A 和 Fig. D per-Tw 需要新增或重算中间表。
```

## 3. 逐图代码检查报告

### Fig. A

当前函数：

```text
plotting.plot_figA_recovery_dynamics()
observables.compute_recovery_dynamics_by_Tw()
```

当前问题：

```text
现在画的是 mean cycle-averaged magnetization，不是 1-CDF。
metadata.recovery_time 当前是 baseline-crossing 定义，不是 M=0 paper-style 定义。
```

现有数据是否足够：

```text
足够。
output/final_simulation/magnetization.csv 保存了每个 run_id 的完整 magnetization time series。
metadata.csv 保存了每个 run_id 的 release snapshot_time。
```

需要新增的计算：

```text
compute_paper_style_recovery_time_from_magnetization()
compute_unrecovered_fraction_by_Tw()
```

推荐输出新表：

```text
output/final_analysis/recovery_survival_M0_by_Tw.csv
```

推荐列：

```text
Tw
recovery_time
n_total
n_recovered_by_time
n_unrecovered
fraction_unrecovered
cdf
survival
definition
```

绘图修改：

```text
plot_figA_recovery_survival()
```

输出建议：

```text
figA_recovery_survival_M0_semilog_loglog.png
```

为保持旧文件名兼容，也可以同时覆盖：

```text
figA_rccn_ageing_reproduction.png
```

实现提醒：

```text
magnetization.csv 很大，约 1.88 GB。
计算 Fig. A 时优先使用 pandas chunksize 或按 run_id/Tw 分块读取，避免一次性读入导致内存压力。
```

### Fig. B

当前函数：

```text
plotting.plot_figB_umap_by_Tw_recovery_time()
```

当前可直接使用的表：

```text
cell_state_table.csv
tail_fraction_by_Tw.csv
```

当前需要改的内容：

```text
1. 替换 0 / 20 / 120 min 颜色
2. 每个 Tw panel 内计算 UMAP centroid
3. 用箭头连接 0 -> 20 -> 120 min centroids
4. 每个 Tw 子图加入 UMAP1 和 UMAP2 的边缘分布
```

不需要重算：

```text
PCA
UMAP
KMeans
simulation
```

推荐颜色：

```text
0 min   #FFB703
20 min  #5A189A
120 min #E63914
```

边缘分布建议：

```text
对每个 Tw panel 单独绘制：
    - 上方 marginal: UMAP1 distribution
    - 右侧 marginal: UMAP2 distribution
    - 按 state_recovery_time = 0, 20, 120 分组着色
    - 使用与 scatter 相同的颜色
    - 可以用 KDE 或 normalized histogram
    - 边缘分布只作为辅助，不遮挡主 scatter
```

实现提醒：

```text
Fig. B 是 3 个 Tw panels。
加入 marginal distributions 后，推荐用 matplotlib GridSpec / nested GridSpec，
让每个 Tw panel 成为一个小的 scatter + top marginal + right marginal 组合。
三组子图仍应共享同一套 UMAP x/y limits，方便比较不同 Tw。
```

推荐输出：

```text
figB_umap_by_Tw_recovery_time.png
```

### Fig. C

当前函数：

```text
plotting.plot_figC_cluster_occupancy_and_lag()
```

当前可直接使用的表：

```text
cluster_summary_by_Tw.csv
cell_state_table.csv
```

当前需要改的内容：

```text
1. 替换 cluster 0/1/2 颜色
2. 左图 legend 移到 plotting area 外
3. 图注/文档说明 cluster 定义
4. 图注/文档说明右图是 lag_time distribution
```

不需要重算：

```text
cluster labels
cluster_summary
cell_state_table
```

推荐颜色：

```text
cluster 0 #4198AC
cluster 1 #7BC0CD
cluster 2 #DBCB92
```

推荐输出：

```text
figC_cluster_occupancy_lag_by_cluster.png
```

### Fig. D

当前函数：

```text
plotting.plot_figD_cycle_groups_along_PC1()
spin_analysis.compute_cycle_pc1_moving_average()
```

当前可直接使用的 mixed-all-`Tw` 表：

```text
cycle_pc1_moving_average.csv
cell_state_table.csv
```

当前 per-`Tw` 图需要的原始表：

```text
cell_state_table.csv
cycle_group_features.csv
```

当前问题：

```text
cycle_pc1_moving_average.csv 没有 Tw 列，因此不能直接筛选出每个 Tw 的 moving average。
```

但现有数据足够，因为：

```text
cell_state_table.csv 有 Tw, run_id, state_recovery_time, PC1
cycle_group_features.csv 有 Tw, run_id, state_recovery_time, short/medium/long_cycle_activation
```

需要新增的计算：

```text
compute_cycle_pc1_moving_average_by_Tw()
```

推荐输出新表：

```text
output/final_analysis/cycle_pc1_moving_average_by_Tw.csv
```

推荐列：

```text
Tw
PC1_window_center
cycle_group
mean_cycle_activation
sem_cycle_activation
n_cells_in_window
window_size
state_recovery_time
```

推荐输出图：

```text
figD_cycle_groups_along_PC1_mixed.png
figD_cycle_groups_along_PC1_Tw0.png
figD_cycle_groups_along_PC1_Tw195.png
figD_cycle_groups_along_PC1_Tw488.png
figD_cycle_groups_along_PC1_Tw1346.png
figD_cycle_groups_along_PC1_Tw1500.png
```

也可以保留原文件名给 mixed 版本：

```text
figD_cycle_groups_along_PC1.png
```

图注必须说明：

```text
y-axis 是 absolute mean cycle magnetization，不是 relative proportion。
当前使用 release-state subset: state_recovery_time = 0。
```

### Fig. E

当前函数：

```text
plotting.plot_figE_presister_like_pca_umap()
```

当前可直接使用的表：

```text
cell_state_table.csv
```

当前需要改的内容：

```text
1. 替换 normal / presister-like 颜色
2. PCA panel 增加 PC1 和 PC2 marginal distributions
3. 保持 marginal distribution 与 scatter 使用相同颜色
4. 图注说明 presister-like 来自 TailFraction rule
```

不需要重算：

```text
PCA
UMAP
presister_like labels
simulation
```

推荐颜色：

```text
normal          #163273
presister-like  #FA517C
```

推荐输出：

```text
figE_presister_like_PCA_UMAP.png
```

## 4. 推荐重画顺序

### Step 1: 先改纯绘图美学和注释，不动计算

优先修改：

```text
Fig. B colors + centroid arrows + marginal distributions
Fig. C colors + outside legend
Fig. E colors + PCA marginal distributions
```

原因：

```text
这些图现有 analysis table 已经足够，不需要重算大表。
改动风险小，能最快得到符合修改要求的新版图。
```

涉及函数：

```text
plot_figB_umap_by_Tw_recovery_time()
plot_figC_cluster_occupancy_and_lag()
plot_figE_presister_like_pca_umap()
```

### Step 2: 重做 Fig. A 的科学量

新增计算函数：

```text
compute_recovery_time_to_M0_by_run()
compute_survival_from_recovery_times()
compute_survival_M0_by_Tw()
```

推荐放置：

```text
src/rccn_persistence/observables.py
```

新增绘图函数：

```text
plot_figA_recovery_survival_semilog_loglog()
```

推荐放置：

```text
src/rccn_persistence/plotting.py
```

脚本修改：

```text
scripts/make_final_project_figures.py
```

或新增轻量脚本：

```text
scripts/recompute_final_figure_tables.py
```

实现原则：

```text
不要重跑 simulation。
直接读取 output/final_simulation/magnetization.csv 和 metadata.csv。
大 CSV 用 chunksize 读取。
```

### Step 3: 生成 Fig. D per-`Tw` 中间表和图

新增计算函数：

```text
compute_cycle_pc1_moving_average_by_Tw()
```

推荐放置：

```text
src/rccn_persistence/spin_analysis.py
```

或作为现有函数的参数化扩展：

```text
compute_cycle_pc1_moving_average(..., Tw=None)
```

新增/修改绘图函数：

```text
plot_figD_cycle_groups_along_PC1(..., title_suffix=None)
plot_figD_cycle_groups_per_Tw()
```

推荐输出：

```text
mixed + five per-Tw PNG files
```

实现原则：

```text
同一套 y-axis definition。
同一套 cycle-group colors。
同一套 state_recovery_time_for_figD = 0。
```

### Step 4: 重新运行绘图脚本

推荐命令：

```powershell
python scripts\make_final_project_figures.py
```

如果新增了独立的中间表重算脚本，则先运行：

```powershell
python scripts\recompute_final_figure_tables.py
python scripts\make_final_project_figures.py
```

### Step 5: 最小验证

重画后检查：

```text
1. output/final_figures/ 下 A-E 文件时间更新
2. Fig. A y-axis 是 1-CDF，不再是 mean magnetization
3. Fig. A 有 semi-log 和 log-log 两个 subplot
4. Fig. B 有新颜色、0 -> 20 -> 120 centroid arrows，以及每个 Tw 子图的 UMAP1/UMAP2 边缘分布
5. Fig. C cluster 颜色正确，legend 不遮挡左图
6. Fig. D mixed 和 per-Tw 文件都存在
7. Fig. D caption / 文档明确 y-axis 是 absolute mean cycle magnetization
8. Fig. E PCA panel 有 marginal distributions
```

## 5. 建议新增输出文件清单

推荐新增分析表：

```text
output/final_analysis/recovery_survival_M0_by_Tw.csv
output/final_analysis/cycle_pc1_moving_average_by_Tw.csv
```

推荐新增/保留图文件：

```text
output/final_figures/figA_rccn_ageing_reproduction.png
output/final_figures/figA_recovery_survival_M0_semilog_loglog.png
output/final_figures/figB_umap_by_Tw_recovery_time.png
output/final_figures/figC_cluster_occupancy_lag_by_cluster.png
output/final_figures/figD_cycle_groups_along_PC1.png
output/final_figures/figD_cycle_groups_along_PC1_Tw0.png
output/final_figures/figD_cycle_groups_along_PC1_Tw195.png
output/final_figures/figD_cycle_groups_along_PC1_Tw488.png
output/final_figures/figD_cycle_groups_along_PC1_Tw1346.png
output/final_figures/figD_cycle_groups_along_PC1_Tw1500.png
output/final_figures/figE_presister_like_PCA_UMAP.png
```

## 6. 不建议现在做的事情

暂时不建议重跑：

```text
scripts/run_final_rccn_simulation.py --preset final
```

原因：

```text
现有全量 simulation 已经成功完成，数据足够支持本轮绘图修订。
重跑会花数小时，且可能引入随机差异。
```

暂时不建议改：

```text
PCA/UMAP/KMeans feature definition
```

原因：

```text
本轮修改要求主要是图形表达和 Fig. A 的 recovery observable 定义。
如果同时改变 feature definition，会让新版图和旧版图差异来源变得不清楚。
```

## 7. 最小执行计划摘要

```text
1. 修改 plotting.py:
   - Fig. B 新颜色 + centroid arrows + UMAP1/UMAP2 marginals for each Tw panel
   - Fig. C 新 cluster colors + outside legend
   - Fig. E 新 colors + PCA marginals

2. 新增 Fig. A M=0 survival 计算:
   - 从 magnetization.csv + metadata.csv 得到 recovery_survival_M0_by_Tw.csv
   - 画 semi-log + log-log 两个 subplot

3. 新增 Fig. D per-Tw moving average:
   - 从 cell_state_table.csv + cycle_group_features.csv 重算 by-Tw table
   - 输出 mixed + five per-Tw plots

4. 运行最终绘图脚本并检查 output/final_figures。
```

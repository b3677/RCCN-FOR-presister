# RCCN Spin-Glass Persistence 项目 Python 架构与文件级伪代码

本文件是后续 Python 重构前的设计文档。它参考三类材料：

1. 项目科学说明：`cowithAI/spin_glass_final_project_description.md`
2. MATLAB 代码阅读报告：`cowithAI/matlab_rccn_code_reading_report.md`
3. 原始 MATLAB 实现：`Original_code_matlab`

本文件只写项目架构和伪代码，不写完整 Python 实现。

## 1. 当前科研目标

本项目的核心目标是用 RCCN / spin-glass 模型研究抗生素 persistence 中的 aging-dependent cell-state heterogeneity。

更具体地说：

1. 复现原 MATLAB RCCN 模型的核心动态。
2. 对不同 waiting time `T_w` 生成模拟细胞的 spin states。
3. 保存 stress removal 时刻的 spin-state snapshot。
4. 计算每个模拟细胞的 recovery / lag time。
5. 对 spin-state matrix 做 PCA / clustering。
6. 检查 spin clusters 是否和 `T_w` 或 recovery time 有关系。

这个 Python 项目在整个科研流程中的位置是：

```text
原论文 / MATLAB 模型
    -> Python 最小复现
    -> 保存 spin-state snapshots
    -> PCA / clustering
    -> cluster 与 recovery time 的关系
    -> final project figures
```

### 1.1 已确认的第一版实现选择

用户已确认第一版按以下选择执行：

1. **ensemble 方式**：复现 MATLAB 默认设置 `different_initial_conditions = false`。也就是不同 run 使用不同随机 network，同时也有不同 initial spins。
2. **trajectory 保存**：第一版不默认保存 full spin trajectory，只保存 release snapshot、early recovery snapshot、magnetization time series 和 metadata。
3. **snapshot 时间点**：
   - release snapshot：`t = init_time + Tw`
   - early recovery snapshot：`t = init_time + Tw + 100`
4. **运行规模**：
   - debug：`num_spins = 512`, `n_runs = 3`, `waiting_times = [20, 40]`
   - small scientific run：`num_spins = 2^14`, `n_runs = 20`, `waiting_times = [20, 160, 640, 3000]`
   - final run：`num_spins = 2^14`, `waiting_times = [20,40,80,160,320,640,1280,3000]`，`n_runs` 根据机器性能决定
5. **`sign(0)` 处理**：如果 local field 恰好为 0，则保留上一时刻 spin，并记录 zero-field 出现次数。
6. **clustering 第一版**：PCA 先降到 10 维，再用 k-means，默认 `K = 3`。最终图至少画 PC1/PC2 colored by `Tw`、cluster、recovery time。

## 2. 输入与输出

### 2.1 输入

第一版 Python 重构不依赖外部实验数据。主要输入是显式写在配置中的模型参数：

| 参数 | 默认值 | 来源 |
|---|---:|---|
| `num_spins` | `2^14` | `initParams.m` |
| `init_time` | `2000` | `initParams.m` |
| `waiting_times` | `[20,40,80,160,320,640,1280,3000]` | `runSimulationExperiments.m` |
| `relax_time` | `9000` | `initParams.m` |
| `gamma` | `1.5` | `initParams.m` |
| `H_init` | `0` | `initParams.m` |
| `H_stress` | `0.8` | `initParams.m` |
| `H_relax` | `0` | `initParams.m` |
| `n_runs` | debug 用 `3`，small run 用 `20`，final run 再扩大 | MATLAB 默认 `run_num=900` |
| `max_cycle_length` | `2500` | `initJij.m` |
| `early_recovery_delta` | `100` | 项目第一版约定 |
| `save_full_trajectory` | `false` | 项目第一版约定 |
| `different_initial_conditions` | `false` | MATLAB 默认 |

为了验证，可以另外读取：

```text
Original_code_matlab/NumericData/T*.mat
```

这些 `.mat` 文件通常保存的是 `mag`，用于比较 recovery / survival curve 的整体趋势。

### 2.2 输出

第一版最小输出：

```text
output/rccn_simulation/
    params.json
    metadata.csv
    magnetization.csv
    spin_release.npy
    spin_early_recovery.npy
```

含义：

| 文件 | 含义 |
|---|---|
| `params.json` | 本次模拟使用的参数 |
| `metadata.csv` | 每个 simulated cell 的 `run_id`, `Tw`, `recovery_time`, `snapshot_time` |
| `magnetization.csv` | 每个 run 的 magnetization time series，或长表格式 |
| `spin_release.npy` | release state spin matrix，行是 run，列是 spin |
| `spin_early_recovery.npy` | stress removal 后 `100` steps 的 spin matrix |

聚类分析输出：

```text
output/spin_clustering/
    pca_scores.csv
    cluster_labels.csv
    cluster_occupancy_by_Tw.csv
    recovery_time_by_cluster.csv
```

图像输出：

```text
output/figures/
    fig1_recovery_survival_by_Tw.png
    fig2_spin_pca_by_Tw.png
    fig3_spin_pca_by_cluster.png
    fig4_spin_pca_by_recovery_time.png
    fig5_cluster_recovery_time.png
```

## 3. 科学原理与数学结构

### 3.1 Spin state

每个 spin 是一个二值状态：

```math
s_i(t) \in \{-1,+1\}
```

在生物学解释中，一个 spin 可以理解为粗粒度的细胞内部组分状态，例如 active / inactive。不要把单个 spin 直接解释成某个具体基因。

### 3.2 RCCN 网络结构

RCCN 是 Randomly Connected Cycles Network。它由许多 feedback cycles 组成。

每个 cycle 的长度为：

```math
L_i
```

MATLAB 中的实际抽样逻辑是：

```matlab
block_size = floor(1/(rand()^(1/0.5)));
while block_size > 2500
    block_size = floor(1/(rand()^(1/0.5)));
end
```

这对应一个重尾的 cycle-length distribution。项目说明里把它概括为：

```math
P(L) \propto L^{-\alpha}, \quad \alpha \approx 1.5
```

Python 重构时应以 MATLAB 代码为实现参考。

### 3.3 Spin update rule

MATLAB 的核心更新在 `dynamicExperiment.m`：

```matlab
loc_field = J_ij * spins + H(exp_part)
spins = sign(loc_field)
```

Python 里应保留同步更新：

```math
\mathbf{s}(t+1)
=
\operatorname{sign}
\left(
J\mathbf{s}(t) + H(t)
\right)
```

默认噪声为 0。

### 3.4 Magnetization

本项目应使用 cycle-averaged magnetization，也就是 MATLAB `getObservables.m` 里的 `mag_B`。

先对每个 cycle 求平均：

```math
m_i(t)
=
\frac{1}{L_i}
\sum_{k=0}^{L_i-1}
s_i^{(k)}(t)
```

再对所有 cycles 平均：

```math
M(t)
=
\frac{1}{N_c}
\sum_{i=1}^{N_c}
m_i(t)
```

不要用简单的 all-spin average 代替它。

### 3.5 Recovery / lag time

MATLAB 的 `getCDF.m` 定义为：

```text
1. 用 stress 前最后 1000 个 time points 估计 baseline magnetization
2. 取 stress removal 后的 magnetization
3. 找第一次低于 baseline 的时间点
```

数学形式：

```math
\tau
=
\min
\{t > T_w : M(t) < M_0\}
- T_w
```

其中：

```math
M_0 = \text{mean baseline magnetization before stress}
```

在代码中，`tau` 是每个 simulated cell 的 first-passage recovery time。

### 3.6 Spin-state clustering

保存 release state：

```math
\mathbf{s}_n(t^*) =
\mathbf{s}_n(t_\text{init}+T_w)
```

把所有 runs 拼成矩阵：

```math
X_\text{spin}
\in
\mathbb{R}^{N_\text{runs} \times N_\text{spins}}
```

然后做 PCA / clustering：

```text
X_spin
    -> center columns
    -> PCA
    -> k-means or hierarchical clustering
    -> cluster occupancy by Tw
    -> recovery time distribution by cluster
```

## 4. 推荐项目架构

推荐使用轻量函数式结构，不做复杂类封装：

```text
src/
    rccn_persistence/
        __init__.py
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

tests/
    test_network_small.py
    test_dynamics_small.py
    test_observables.py

notebooks/
    01_validate_matlab_numericdata.ipynb
    02_explore_spin_clustering.ipynb
```

第一版真正必须实现的文件是：

```text
config.py
network.py
dynamics.py
observables.py
simulation.py
io_utils.py
spin_analysis.py
run_rccn_simulation.py
run_spin_clustering.py
```

`plotting.py`、`tests/`、`notebooks/` 很重要，但可以在核心模拟跑通后逐步补。

## 5. MATLAB 到 Python 的对应关系

| MATLAB 文件 | Python 文件 | 迁移含义 |
|---|---|---|
| `initParams.m` | `config.py` | 保存模型参数和默认实验协议 |
| `initJij.m` | `network.py` | 构建 cycles、`JInfo`、inter-cycle coupling |
| `genShiftMat.m` | `network.py` | 构建 cycle 内 shift matrix 或等价 sparse matrix |
| `initSpins.m` | `dynamics.py` | 初始化 `-1/+1` spin vector |
| `dynamicExperiment.m` | `dynamics.py`, `simulation.py` | 执行三阶段同步更新并保存 snapshots |
| `getObservables.m` | `observables.py` | 计算 cycle-averaged magnetization |
| `getCDF.m` | `observables.py` | 计算 recovery time 和 survival curve |
| `getObservablesForMultipleTw.m` | `simulation.py`, `run_rccn_simulation.py` | 多 `T_w` 批量运行 |
| `ShowSimulationData.m` | `plotting.py`, `make_project_figures.py` | 画 survival / magnetization / clustering figures |

## 6. 文件级 Python 伪代码

下面是每个文件的建议内容。伪代码只描述逻辑，不是可直接运行的 Python。

## File: `src/rccn_persistence/config.py`

**作用：**
集中保存默认参数，让模拟协议一眼可见。

**输入：**
无外部数据输入。用户可以手动修改默认参数。

**输出：**
一个简单参数对象或字典，例如 `params`。

**伪代码：**

```text
function make_default_params():
    1. 设置 num_spins = 2^14
    2. 设置 init_time = 2000
    3. 设置 relax_time = 9000
    4. 设置 waiting_times = [20,40,80,160,320,640,1280,3000]
    5. 设置 gamma = 1.5
    6. 设置 H_init = 0
    7. 设置 H_stress = 0.8
    8. 设置 H_relax = 0
    9. 设置 max_cycle_length = 2500
    10. 设置 n_runs；debug 用 3，small scientific run 用 20，final run 再扩大
    11. 设置 save_full_trajectory = false
    12. 设置 release_snapshot = true
    13. 设置 early_recovery_delta = 100
    14. 设置 save_early_recovery_snapshot = true
    15. 设置 different_initial_conditions = false，复现 MATLAB 默认 ensemble
    16. 设置 pca_components = 10
    17. 设置 n_clusters = 3
    18. 返回 params
```

```text
function make_output_paths(project_root):
    1. 从 project_root 构造 output/rccn_simulation
    2. 构造 output/spin_clustering
    3. 构造 output/figures
    4. 返回 paths
```

**代码类型标注：**
配置逻辑；主干辅助。

**复杂度提醒：**
保持简单字典即可，不需要复杂配置系统。

## File: `src/rccn_persistence/network.py`

**作用：**
复现 MATLAB `initJij.m` 的网络构建：cycle length、cycle 起点、cycle 内 shift、cycle 间随机耦合。

**输入：**

- `num_spins`
- `gamma`
- `max_cycle_length`
- random number generator

**输出：**

- `J`：建议第一版用 sparse matrix
- `cycle_starts`
- `cycle_lengths`
- `coupling_indices`
- `jinfo` 或等价表格

**伪代码：**

```text
function sample_cycle_lengths(num_spins, max_cycle_length, rng):
    1. 初始化 cycle_lengths = []
    2. 初始化 total = 0
    3. 当 total < num_spins:
        3.1 从 MATLAB 等价公式抽样 block_size
        3.2 如果 block_size > max_cycle_length，重新抽样
        3.3 如果 total + block_size 超过 num_spins，就截断到剩余 spins
        3.4 把 block_size 加入 cycle_lengths
        3.5 更新 total
    4. 返回 cycle_lengths
```

```text
function make_cycle_starts(cycle_lengths):
    1. 第一个 cycle 从 0 开始
    2. 后续 cycle 的起点是前面 lengths 的累计和
    3. 返回 cycle_starts
```

```text
function choose_coupling_indices(cycle_starts, cycle_lengths, rng):
    1. 初始化 coupling_indices = []
    2. 对每个 cycle:
        2.1 如果 cycle length > 1:
            2.1.1 在该 cycle 的 spin index 范围内随机选一个 spin
            2.1.2 加入 coupling_indices
    3. 返回 coupling_indices
```

```text
function build_shift_edges(cycle_starts, cycle_lengths):
    1. 初始化 row_indices, col_indices, values
    2. 对每个 cycle:
        2.1 对 cycle 内每个位置 k:
            2.1.1 找到当前 spin 和它应该接收输入的上一个 spin
            2.1.2 添加一条权重为 1 的 shift edge
    3. 返回 shift edge lists
```

```text
function build_intercycle_edges(coupling_indices, gamma, num_cycles, rng):
    1. 初始化 row_indices, col_indices, values
    2. 对 coupling_indices 中每个 target spin:
        2.1 对 coupling_indices 中每个 source spin:
            2.1.1 从 Normal(0, gamma / sqrt(num_cycles)) 抽样权重
            2.1.2 添加从 source 到 target 的 edge
    3. 返回 inter-cycle edge lists
```

```text
function build_rccn_network(params, rng):
    1. 调用 sample_cycle_lengths
    2. 调用 make_cycle_starts
    3. 调用 choose_coupling_indices
    4. 调用 build_shift_edges
    5. 调用 build_intercycle_edges
    6. 合并 shift edges 和 inter-cycle edges
    7. 构造 sparse J matrix
    8. 构造 jinfo：每个 spin 的 cycle_start 和 cycle_length
    9. 返回 network
```

**代码类型标注：**
科学主干逻辑。

**复杂度提醒：**
这是最容易出错的文件。重点检查 MATLAB 1-based indexing 到 Python 0-based indexing 的转换。第一版建议用 toy network 验证 shift 方向。

## File: `src/rccn_persistence/dynamics.py`

**作用：**
复现 MATLAB `initSpins.m` 和 `dynamicExperiment.m` 的 spin 初始化与同步更新。

**输入：**

- `J`
- `num_spins`
- `init_time`
- `Tw`
- `relax_time`
- `H_init`, `H_stress`, `H_relax`
- random number generator

**输出：**

- magnetization 计算所需的 sampled states 或 full trajectory
- release snapshot
- early recovery snapshot，固定为 stress removal 后 100 steps
- final spin state

**伪代码：**

```text
function initialize_spins(num_spins, rng):
    1. 对每个 spin 抽样一个随机数
    2. 如果随机数小于 0.5，设为 +1 或 -1
    3. 生成长度为 num_spins 的 spin vector
    4. 返回 spins
```

```text
function sign_without_zero_problem(local_field, previous_spins):
    1. 对 local_field > 0 的位置设为 +1
    2. 对 local_field < 0 的位置设为 -1
    3. 对 local_field == 0 的位置保留 previous_spins
    4. 统计 zero-field 出现次数
    5. 返回 new_spins 和 zero_field_count
```

```text
function update_spins_once(spins, J, H):
    1. 计算 local_field = J @ spins + H
    2. 调用 sign_without_zero_problem
    3. 返回 new_spins 和 zero_field_count
```

```text
function run_stage(spins, J, H, n_steps, observer):
    1. 对 step 从 1 到 n_steps:
        1.1 如果 observer 需要当前状态，则把当前 spins 交给 observer
        1.2 调用 update_spins_once 更新 spins
    2. 返回 stage 结束后的 spins
```

```text
function run_one_protocol(network, params, Tw, rng):
    1. 初始化 spins
    2. 初始化一个 trajectory observer，用于计算 magnetization 和保存 snapshot
    3. 运行 init stage：H = 0，长度 init_time
    4. 运行 stress stage：H = H_stress，长度 Tw
    5. 在 stress stage 结束位置保存 release_spin_snapshot
    6. 运行 relax stage：H = 0，长度 relax_time
    7. 在 stress removal 后 100 steps 保存 early_recovery_snapshot
    8. 在整个过程中保存 magnetization 所需的信息
    9. 统计整个 run 中 zero-field 出现次数
    10. 返回 simulation_result
```

**代码类型标注：**
科学主干逻辑。

**复杂度提醒：**
不要一开始保存所有 runs 的完整 `spins_hist`。第一版在运行时逐步计算 magnetization，并只保存 release snapshot、early recovery snapshot 和 metadata。

## File: `src/rccn_persistence/observables.py`

**作用：**
计算 magnetization、recovery time、CDF / survival curve。对应 MATLAB `getObservables.m` 和 `getCDF.m`。

**输入：**

- spin vector 或 spin trajectory
- `cycle_starts`
- `cycle_lengths`
- `init_time`
- `Tw`
- magnetization time series

**输出：**

- `magnetization`
- `recovery_time`
- `cdf`
- `survival`

**伪代码：**

```text
function compute_cycle_magnetization(spins, cycle_starts, cycle_lengths):
    1. 初始化 cycle_mags = []
    2. 对每个 cycle:
        2.1 取出该 cycle 对应的 spin slice
        2.2 计算这个 cycle 内 spins 的平均值
        2.3 加入 cycle_mags
    3. 返回 cycle_mags
```

```text
function compute_global_magnetization(spins, cycle_starts, cycle_lengths):
    1. 调用 compute_cycle_magnetization
    2. 对所有 cycle_mags 求平均
    3. 返回 M
```

```text
function compute_magnetization_series(spin_series, cycle_starts, cycle_lengths):
    1. 初始化 mag = []
    2. 对每个 time point:
        2.1 取出该 time point 的 spin vector
        2.2 调用 compute_global_magnetization
        2.3 把结果加入 mag
    3. 返回 mag
```

```text
function compute_baseline_magnetization(mag, init_time, baseline_window):
    1. 取 stress 前 baseline_window 个点
    2. 计算平均值
    3. 返回 m_base
```

```text
function compute_recovery_time(mag, init_time, Tw, baseline_window):
    1. 调用 compute_baseline_magnetization 得到 m_base
    2. 从 index = init_time + Tw 开始截取 relaxation magnetization
    3. 对每个 relaxation time point:
        3.1 如果 M(t) - m_base < 0:
            3.1.1 返回当前 relaxation index，作为 recovery_time
    4. 如果一直没有 crossing:
        4.1 返回 missing 或 relax_time + 1
        4.2 在 metadata 中标记 recovered = false
```

```text
function compute_recovery_cdf(recovery_times, max_time):
    1. 创建从 1 到 max_time 的 time grid
    2. 对每个 t:
        2.1 计算 recovery_times <= t 的比例
    3. 返回 cdf table
```

```text
function compute_survival_curve(recovery_times, max_time):
    1. 调用 compute_recovery_cdf
    2. survival = 1 - cdf
    3. 返回 survival table
```

**代码类型标注：**
科学主干逻辑；统计摘要。

**复杂度提醒：**
`compute_recovery_time` 必须和 MATLAB `getCDF.m` 对齐。尤其注意 `< baseline` 还是 `<= baseline`，第一版按 MATLAB 使用 `<`。

## File: `src/rccn_persistence/simulation.py`

**作用：**
组织一个 run、一个 `T_w`、一批 `T_w` 的完整模拟流程。对应 MATLAB `runSimulationExperiments.m` 和 `getObservablesForMultipleTw.m`。

**输入：**

- `params`
- output paths
- random seed

**输出：**

- 所有 runs 的 metadata
- magnetization table
- release spin matrix
- early recovery matrix

**伪代码：**

```text
function run_one_cell(params, Tw, run_id, rng):
    1. 按 MATLAB 默认 ensemble，每个 run 生成一个新的随机 network
    2. 调用 build_rccn_network
    3. 调用 run_one_protocol 生成 spin dynamics summary
    4. 从 magnetization series 计算 recovery_time
    5. 整理 metadata row:
        5.1 run_id
        5.2 Tw
        5.3 recovery_time
        5.4 recovered
        5.5 snapshot_time
        5.6 network_id
        5.7 early_recovery_snapshot_time = init_time + Tw + 100
        5.8 zero_field_count
    6. 返回 cell_result
```

```text
function run_for_one_waiting_time(params, Tw, n_runs, rng):
    1. 初始化结果列表
    2. 对 run_id 从 1 到 n_runs:
        2.1 调用 run_one_cell
        2.2 收集 metadata
        2.3 收集 magnetization
        2.4 收集 release snapshot
        2.5 收集 early recovery snapshot
    3. 拼接 release snapshots 成 matrix
    4. 拼接 early recovery snapshots 成 matrix
    5. 返回 Tw_result
```

```text
function run_batch(params, paths):
    1. 初始化总 metadata
    2. 初始化总 magnetization table
    3. 初始化总 release snapshot matrix
    4. 初始化总 early recovery snapshot matrix
    5. 对每个 Tw:
        5.1 调用 run_for_one_waiting_time
        5.2 合并结果
        5.3 每个 Tw 结束后立即保存一次中间结果
    6. 保存最终结果
    7. 返回 batch_result
```

**代码类型标注：**
主流程编排；小批量自动化。

**复杂度提醒：**
这里可以有少量进度打印。不要写复杂日志系统。批量运行时可以让单个 run 报错直接停下，先保证科学结果可检查。

## File: `src/rccn_persistence/io_utils.py`

**作用：**
负责保存和读取结果。保持简单、显式、可追踪。

**输入：**

- params
- metadata table
- magnetization table
- spin matrices
- output paths

**输出：**

- 文件写入磁盘
- 从磁盘读取后的对象

**伪代码：**

```text
function ensure_output_dirs(paths):
    1. 创建 simulation output directory
    2. 创建 clustering output directory
    3. 创建 figures directory
```

```text
function save_params(params, path):
    1. 把 params 转成容易阅读的 JSON
    2. 保存到 params.json
```

```text
function save_simulation_outputs(batch_result, paths):
    1. 保存 metadata.csv
    2. 保存 magnetization.csv
    3. 保存 spin_release.npy
    4. 如果有 early recovery snapshot，保存 spin_early_recovery.npy
```

```text
function load_simulation_outputs(paths):
    1. 读取 metadata.csv
    2. 读取 magnetization.csv
    3. 读取 spin_release.npy
    4. 返回 simulation_data
```

**代码类型标注：**
保存输出；辅助逻辑。

**复杂度提醒：**
不要自动搜索很多路径。路径应由 `config.py` 或脚本显式传入。

## File: `src/rccn_persistence/spin_analysis.py`

**作用：**
对 release spin-state matrix 做 PCA、聚类和 cluster-level summary。

**输入：**

- `X_spin_release`
- `metadata`
- number of PCA components
- number of clusters

**输出：**

- PCA scores
- cluster labels
- cluster occupancy by `Tw`
- recovery time summary by cluster

**伪代码：**

```text
function center_spin_matrix(X_spin):
    1. 对每个 spin column 计算平均值
    2. 每个元素减去对应 column mean
    3. 返回 centered matrix
```

```text
function run_pca_on_spins(X_spin, n_components):
    1. 调用 center_spin_matrix
    2. 执行 PCA
    3. 返回 pca_scores 和 explained_variance
```

```text
function cluster_pca_scores(pca_scores, n_clusters):
    1. 取前 10 个 PC scores
    2. 运行 k-means，第一版默认 K = 3
    3. 返回 cluster_labels
```

```text
function summarize_cluster_occupancy(metadata, cluster_labels):
    1. 把 cluster_labels 加入 metadata
    2. 按 Tw 和 cluster 分组计数
    3. 对每个 Tw 计算 cluster fraction
    4. 返回 occupancy table
```

```text
function summarize_recovery_by_cluster(metadata, cluster_labels):
    1. 把 cluster_labels 加入 metadata
    2. 按 cluster 分组
    3. 计算 recovery_time 的 mean, median, count
    4. 可选计算每个 cluster 内不同 Tw 的 recovery summary
    5. 返回 summary table
```

```text
function run_spin_clustering_analysis(simulation_data, analysis_params):
    1. 读取 X_spin_release 和 metadata
    2. 调用 run_pca_on_spins
    3. 调用 cluster_pca_scores
    4. 调用 summarize_cluster_occupancy
    5. 调用 summarize_recovery_by_cluster
    6. 返回 analysis_result
```

**代码类型标注：**
数据分析主干逻辑。

**复杂度提醒：**
第一版只用 PCA + k-means，默认 `n_components = 10`，`K = 3`。UMAP、hierarchical clustering 可以作为后续扩展，不要第一版同时全部实现。

## File: `src/rccn_persistence/plotting.py`

**作用：**
画最终项目需要的主要图。

**输入：**

- survival curve table
- PCA scores
- metadata
- cluster labels
- occupancy table
- recovery summary

**输出：**

- `.png` 或 `.pdf` 图像文件

**伪代码：**

```text
function plot_survival_by_Tw(survival_table, output_path):
    1. 对每个 Tw:
        1.1 取出该 Tw 的 survival curve
        1.2 画 survival vs time
    2. 设置 x/y 轴标签
    3. 保存图
```

```text
function plot_pca_by_Tw(pca_scores, metadata, output_path):
    1. 把 PC1, PC2 和 Tw 合并
    2. 画 PC1 vs PC2 scatter
    3. 颜色表示 Tw
    4. 保存图
```

```text
function plot_pca_by_cluster(pca_scores, cluster_labels, output_path):
    1. 把 PC1, PC2 和 cluster label 合并
    2. 画 PC1 vs PC2 scatter
    3. 颜色表示 cluster
    4. 保存图
```

```text
function plot_pca_by_recovery_time(pca_scores, metadata, output_path):
    1. 把 PC1, PC2 和 recovery_time 合并
    2. 画 PC1 vs PC2 scatter
    3. 颜色表示 recovery_time
    4. 保存图
```

```text
function plot_cluster_occupancy(occupancy_table, output_path):
    1. 对每个 Tw 显示各 cluster fraction
    2. 使用 bar plot 或 line plot
    3. 保存图
```

```text
function plot_recovery_by_cluster(metadata_with_cluster, output_path):
    1. 按 cluster 画 recovery_time 分布
    2. 可用 boxplot 或 violin plot
    3. 保存图
```

**代码类型标注：**
绘图逻辑。

**复杂度提醒：**
绘图函数不要承担计算任务。计算结果应先在 `observables.py` 或 `spin_analysis.py` 中完成。

## File: `scripts/run_rccn_simulation.py`

**作用：**
模拟主入口。对应 MATLAB `runSimulationExperiments.m`。

**输入：**

- 用户手动指定 project root
- 可选指定 n_runs、waiting_times、random seed

**输出：**

- simulation output files

**伪代码：**

```text
function main():
    1. 设置 project_root
    2. 调用 make_default_params
    3. 如果是测试运行，手动把 n_runs 改小
    4. 调用 make_output_paths
    5. 调用 ensure_output_dirs
    6. 调用 save_params
    7. 调用 run_batch
    8. 调用 save_simulation_outputs
    9. 打印输出文件位置
```

**代码类型标注：**
脚本入口；主流程。

**复杂度提醒：**
不要让这个脚本变成大杂烩。所有科学计算放回 `src/rccn_persistence/`。

## File: `scripts/run_spin_clustering.py`

**作用：**
读取模拟结果，运行 PCA / clustering，保存分析表格。

**输入：**

- simulation output directory
- `n_components`
- `n_clusters`

**输出：**

- clustering output files

**伪代码：**

```text
function main():
    1. 设置 project_root
    2. 设置 simulation output path
    3. 设置 clustering output path
    4. 调用 load_simulation_outputs
    5. 设置 analysis_params
    6. 调用 run_spin_clustering_analysis
    7. 保存 pca_scores.csv
    8. 保存 cluster_labels.csv
    9. 保存 cluster_occupancy_by_Tw.csv
    10. 保存 recovery_time_by_cluster.csv
```

**代码类型标注：**
分析脚本入口。

**复杂度提醒：**
第一版不要自动尝试很多 cluster 数。先固定一个小的 `K`，看图和 summary 再决定是否扩展。

## File: `scripts/make_project_figures.py`

**作用：**
从 simulation 和 clustering 输出中生成最终报告图。

**输入：**

- simulation outputs
- clustering outputs

**输出：**

- final figure files

**伪代码：**

```text
function main():
    1. 设置 project_root
    2. 读取 metadata, magnetization, pca_scores, cluster_labels
    3. 从 recovery_time 计算 survival curves
    4. 调用 plot_survival_by_Tw
    5. 调用 plot_pca_by_Tw
    6. 调用 plot_pca_by_cluster
    7. 调用 plot_pca_by_recovery_time
    8. 调用 plot_cluster_occupancy
    9. 调用 plot_recovery_by_cluster
    10. 打印 figures 路径
```

**代码类型标注：**
绘图脚本入口。

**复杂度提醒：**
不要在这里重新跑模拟或重新做 PCA。它只读取已有结果并画图。

## File: `tests/test_network_small.py`

**作用：**
用小网络检查 cycle construction 和 shift direction。

**输入：**

- 手工设定的小 cycle lengths

**输出：**

- 测试是否通过

**伪代码：**

```text
function test_cycle_lengths_cover_all_spins():
    1. 用小 num_spins 生成 cycle_lengths
    2. 检查 sum(cycle_lengths) == num_spins
```

```text
function test_shift_edges_for_one_cycle():
    1. 构造一个长度为 4 的 cycle
    2. 手工给定 spins
    3. 用 build_shift_edges 生成 J
    4. 计算 J @ spins
    5. 检查结果是否符合预期的 cycle shift
```

**代码类型标注：**
可选检查；科学正确性保护。

**复杂度提醒：**
这是防止 MATLAB/Python indexing 错误的关键测试。

## File: `tests/test_dynamics_small.py`

**作用：**
验证同步更新规则。

**输入：**

- 小的固定 `J`
- 固定 initial spins
- 固定 `H`

**输出：**

- 测试是否通过

**伪代码：**

```text
function test_update_spins_once_matches_manual_calculation():
    1. 设置一个 3x3 或 4x4 的 J
    2. 设置 spins
    3. 设置 H
    4. 手工计算 local_field
    5. 手工计算 expected_sign
    6. 调用 update_spins_once
    7. 检查结果等于 expected_sign
```

**代码类型标注：**
可选检查；科学正确性保护。

**复杂度提醒：**
重点测试同步更新，不测试随机大网络。

## File: `tests/test_observables.py`

**作用：**
验证 cycle-averaged magnetization 和 recovery time。

**输入：**

- 手工构造的 small spins
- 手工构造的 magnetization series

**输出：**

- 测试是否通过

**伪代码：**

```text
function test_cycle_averaged_magnetization():
    1. 设置两个 cycles，例如长度 2 和 4
    2. 手工设置 spins
    3. 手工计算每个 cycle 的平均 spin
    4. 手工计算所有 cycles 的平均
    5. 调用 compute_global_magnetization
    6. 检查结果一致
```

```text
function test_recovery_time_first_crossing():
    1. 构造一个 mag series
    2. 设置 init_time 和 Tw
    3. 手工确定 baseline
    4. 手工确定第一次 crossing
    5. 调用 compute_recovery_time
    6. 检查 recovery_time 一致
```

**代码类型标注：**
可选检查；科学正确性保护。

**复杂度提醒：**
这两个测试比大规模统计复现更重要，因为它们直接保护科学定义。

## File: `notebooks/01_validate_matlab_numericdata.ipynb`

**作用：**
用 MATLAB `NumericData/T*.mat` 验证 Python observable 逻辑，尤其是 recovery CDF / survival curve。

**Notebook cell 伪代码：**

```text
Cell 1: imports and paths
    1. 设置 MATLAB NumericData 路径
    2. 设置 output 路径

Cell 2: load MATLAB mag data
    1. 读取一个或多个 T*.mat
    2. 提取 mag

Cell 3: compute recovery curves
    1. 对每个 Tw 调用 compute_recovery_time
    2. 调用 compute_survival_curve

Cell 4: plot validation
    1. 画 survival curves
    2. 和 MATLAB README / ShowSimulationData 的预期趋势比较

Cell 5: notes
    1. 记录是否趋势一致
    2. 记录任何不一致的原因
```

**代码类型标注：**
验证 notebook；可选但推荐。

**复杂度提醒：**
不要在 notebook 里实现核心函数。核心函数应该从 `src/rccn_persistence` 导入。

## File: `notebooks/02_explore_spin_clustering.ipynb`

**作用：**
交互式查看 spin PCA 和 clustering 结果，辅助选择 final figures。

**Notebook cell 伪代码：**

```text
Cell 1: imports and paths
    1. 设置 simulation output 路径
    2. 设置 clustering output 路径

Cell 2: load spin matrix and metadata
    1. 读取 spin_release.npy
    2. 读取 metadata.csv

Cell 3: run or load PCA
    1. 如果已有 pca_scores.csv，就读取
    2. 否则调用 run_pca_on_spins

Cell 4: visualize by Tw
    1. 画 PC1 / PC2
    2. 颜色表示 Tw

Cell 5: visualize by recovery time
    1. 画 PC1 / PC2
    2. 颜色表示 recovery_time

Cell 6: cluster summary
    1. 查看 cluster occupancy by Tw
    2. 查看 recovery time by cluster
```

**代码类型标注：**
探索 notebook；可选。

**复杂度提醒：**
Notebook 里可以探索，但不要把唯一可复现的主流程只放在 notebook 里。

## 7. 最小实现顺序

建议按下面顺序写代码：

1. `config.py`
2. `network.py`
3. `dynamics.py`
4. `observables.py`
5. `tests/test_network_small.py`
6. `tests/test_dynamics_small.py`
7. `tests/test_observables.py`
8. `simulation.py`
9. `io_utils.py`
10. `scripts/run_rccn_simulation.py`
11. `spin_analysis.py`
12. `scripts/run_spin_clustering.py`
13. `plotting.py`
14. `scripts/make_project_figures.py`

不要一开始就追求 900 runs。推荐运行规模：

```text
debug:
    num_spins = 512
    n_runs = 3
    waiting_times = [20, 40]

small scientific run:
    num_spins = 2^14
    n_runs = 20
    waiting_times = [20, 160, 640, 3000]

final run:
    num_spins = 2^14
    n_runs 根据时间和机器性能决定
    waiting_times = [20,40,80,160,320,640,1280,3000]
```

## 8. 已确认实现细节

以下细节已经由用户确认，后续写代码按这里执行：

1. **`sign(0)` 的处理**
   - MATLAB `sign(0)` 会返回 0。
   - 但 spin model 期望状态是 `-1/+1`。
   - 在随机连续耦合下严格为 0 的概率很低，但不是逻辑上不可能。
   - 第一版如果出现 `local_field == 0`，保留上一时刻 spin，并在 metadata 或 summary 中记录 zero-field 出现次数。

2. **是否保存 full trajectory**
   - MATLAB 原始代码保存完整 `spins_hist`。
   - 本项目 clustering 最需要 release snapshot。
   - 第一版不默认保存 full trajectory。
   - 第一版保存 release snapshot、early recovery snapshot、magnetization time series 和 metadata。

3. **network ensemble 的定义**
   - MATLAB 默认 `different_initial_conditions = false`，即每个 run 生成不同 network。
   - 第一版复现 MATLAB 默认：不同 run 使用不同随机 network，同时也有不同 initial spins。

4. **早期恢复 snapshot 的时间**
   - release snapshot 必须保存。
   - early recovery snapshot 第一版固定为 stress removal 后 100 steps。
   - 也就是绝对时间 `init_time + Tw + 100`。

5. **运行规模**
   - debug：`num_spins = 512`, `n_runs = 3`, `waiting_times = [20, 40]`
   - small scientific run：`num_spins = 2^14`, `n_runs = 20`, `waiting_times = [20, 160, 640, 3000]`
   - final run：`num_spins = 2^14`, `waiting_times = [20,40,80,160,320,640,1280,3000]`，`n_runs` 根据机器性能决定。

6. **clustering 第一版**
   - PCA 先降到 10 维。
   - k-means 默认 `K = 3`。
   - 至少输出 PC1/PC2 colored by `Tw`、cluster、recovery time。

7. **是否加入 PETRI-seq 数据分析**
   - 第一版 Python 架构先不加入 PETRI-seq。
   - 先完成 model-side spin clustering。
   - expression data 比较可以作为第二阶段单独设计。

## 9. 给写代码阶段的执行说明

后续写代码时请遵守：

1. 先实现小网络 deterministic tests。
2. 再实现大网络随机模拟。
3. 先复现 `mag_B` 和 recovery time。
4. 再保存 spin-state matrix。
5. 再做 PCA / clustering。
6. 不要在第一版加入复杂配置系统、复杂日志系统或自定义异常类。
7. 文件不存在、字段缺失、维度不一致可以直接报错。
8. 每个函数都应能对应到一个科学概念：network、spin update、magnetization、recovery time、clustering。

一句话目标：

```text
让 Python 代码成为一份可检查的科研流程笔记：
从 RCCN 动态方程出发，生成 spin states，计算 recovery time，再检验 spin-state clusters 是否对应 aging 和 slow recovery。
```

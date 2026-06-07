# RCCN-FOR-presister

本项目是一个用 Python 复现和扩展 RCCN / spin-glass 模型的小型科研代码库，用于研究抗生素 persistence 中 aging-dependent cell-state heterogeneity。

第一版代码的目标不是做复杂软件框架，而是形成一条可检查、可修改、可复现的科研分析流程：

1. 构建 randomly connected cycles network；
2. 模拟 initialization、stress、relaxation 三阶段 spin dynamics；
3. 保存 stress release 时刻和 early recovery 时刻的 spin-state snapshots；
4. 计算 cycle-averaged magnetization 和 recovery / lag time；
5. 对 release spin states 做 PCA 和 k-means clustering；
6. 输出 summary tables 和 project figures。

## 项目结构

```text
qbio_final_project/
    cowithAI/
        spin_glass_final_project_description.md
        matlab_rccn_code_reading_report.md
        python_rccn_project_architecture_and_pseudocode.md

    Original_code_matlab/
        initParams.m
        initJij.m
        dynamicExperiment.m
        getObservables.m
        getCDF.m
        NumericData/

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

    notebooks/
        01_run_rccn_pipeline_and_view_results.ipynb
        set4.ipynb

    tests/
        test_network_small.py
        test_dynamics_small.py
        test_observables.py

    output/
        rccn_simulation/
        spin_clustering/
        figures/
```

## 关键文件说明

### 科学设计文档

- `cowithAI/spin_glass_final_project_description.md`：项目科学背景和研究问题。
- `cowithAI/matlab_rccn_code_reading_report.md`：原始 MATLAB 代码阅读记录。
- `cowithAI/python_rccn_project_architecture_and_pseudocode.md`：Python 第一版架构和函数级伪代码。

### 核心 Python 模块

- `src/rccn_persistence/config.py`：默认参数、debug 参数、输出路径。
- `src/rccn_persistence/network.py`：RCCN 网络构建，包括 cycle length、cycle start、coupling index 和 sparse interaction matrix `J`。
- `src/rccn_persistence/dynamics.py`：spin 初始化、同步更新规则、release / early recovery snapshot 保存。
- `src/rccn_persistence/observables.py`：cycle-averaged magnetization、recovery time、CDF、survival curve。
- `src/rccn_persistence/simulation.py`：单个 simulated cell、单个 `T_w`、整批 `T_w` 的模拟流程。
- `src/rccn_persistence/io_utils.py`：保存和读取模拟输出。
- `src/rccn_persistence/spin_analysis.py`：release spin matrix 的 PCA 和 k-means clustering。
- `src/rccn_persistence/plotting.py`：项目图像绘制函数。

### 脚本入口

- `scripts/run_rccn_simulation.py`：运行模拟并保存结果。
- `scripts/run_spin_clustering.py`：读取模拟结果，运行 PCA / clustering，并保存表格。
- `scripts/make_project_figures.py`：读取已有输出并生成项目图像。

## 关键参数在哪里

主要参数集中在：

```text
src/rccn_persistence/config.py
```

其中：

- `make_default_params()`：默认科学运行参数。
- `make_debug_params()`：快速检查 pipeline 的小规模参数。
- `make_output_paths(project_root)`：统一定义输出路径。

重要参数如下：

| 参数 | 含义 | 默认值 |
|---|---|---:|
| `num_spins` | 每个 RCCN 网络的 spin 数量 | `2**14` |
| `init_time` | stress 前的初始化 / relaxation 时间 | `2000` |
| `relax_time` | stress removal 后的 relaxation 时间 | `9000` |
| `waiting_times` | stress 持续时间 `T_w` | `[20, 40, 80, 160, 320, 640, 1280, 3000]` |
| `gamma` | cycle 间随机耦合强度 | `1.5` |
| `H_init` | 初始化阶段外场 | `0.0` |
| `H_stress` | stress 阶段外场 | `0.8` |
| `H_relax` | stress removal 后外场 | `0.0` |
| `n_runs` | 每个 `T_w` 下 simulated cells 数量 | `20` |
| `max_cycle_length` | 最大 cycle length | `2500` |
| `early_recovery_delta` | stress removal 后多久保存 early snapshot | `100` |
| `baseline_window` | stress 前用于估计 baseline magnetization 的窗口 | `1000` |
| `pca_components` | PCA 保留维度 | `10` |
| `n_clusters` | k-means cluster 数量 | `3` |
| `random_seed` | 随机种子 | `1` |

## 输出路径和文件

输出路径由 `make_output_paths(project_root)` 统一定义。

### 模拟输出

保存到：

```text
output/rccn_simulation/
```

文件包括：

- `params.json`：本次运行使用的参数。
- `metadata.csv`：每个 simulated cell 一行，包含 `run_id`、`Tw`、`recovery_time`、`recovered`、snapshot 时间和 `zero_field_count`。
- `magnetization.csv`：长表格格式的 magnetization time series，包含 `run_id`、`Tw`、`time`、`magnetization`。
- `spin_release.npy`：stress removal 时刻的 spin-state matrix，形状为 `(n_cells, num_spins)`。
- `spin_early_recovery.npy`：stress removal 后 `early_recovery_delta` steps 的 spin-state matrix。

### 聚类输出

保存到：

```text
output/spin_clustering/
```

文件包括：

- `pca_scores.csv`：每个 simulated cell 的 PCA 坐标。
- `pca_explained_variance.csv`：各 PC 的 explained variance ratio。
- `cluster_labels.csv`：每个 simulated cell 的 k-means cluster label。
- `cluster_occupancy_by_Tw.csv`：不同 `T_w` 下 cluster 占比。
- `recovery_time_by_cluster.csv`：不同 cluster 的 recovery time summary。

### 图像输出

保存到：

```text
output/figures/
```

当前图像包括：

- `fig1_recovery_survival_by_Tw.png`
- `fig2_spin_pca_by_Tw.png`
- `fig3_spin_pca_by_cluster.png`
- `fig4_spin_pca_by_recovery_time.png`
- `fig5_cluster_occupancy_by_Tw.png`

## 快速运行

运行测试：

```powershell
python -m pytest tests
```

运行一个非常小的 smoke test：

```powershell
python scripts\run_rccn_simulation.py --preset debug --num-spins 64 --n-runs 2 --waiting-times 3 5 --init-time 20 --relax-time 120 --early-recovery-delta 10 --baseline-window 10
python scripts\run_spin_clustering.py
python scripts\make_project_figures.py
```

运行默认 debug pipeline：

```powershell
python scripts\run_rccn_simulation.py --preset debug
python scripts\run_spin_clustering.py
python scripts\make_project_figures.py
```

如果要做更大的科学运行，可以直接修改 `src/rccn_persistence/config.py`，或者通过 `scripts/run_rccn_simulation.py` 的命令行参数覆盖关键设置。

## Notebook 入口

新增 notebook：

```text
notebooks/01_run_rccn_pipeline_and_view_results.ipynb
```

它用于：

1. 导入主函数；
2. 查看和修改关键参数；
3. 可选运行模拟；
4. 读取 `output/rccn_simulation/` 结果；
5. 展示 `metadata`、`magnetization` 和 spin snapshot shape；
6. 运行 PCA / clustering；
7. 画出 magnetization、PCA 和 recovery survival 的快速预览图。

默认情况下，notebook 不会自动启动长时间模拟。需要重新跑模拟时，把 notebook 中的：

```python
RUN_SIMULATION = False
```

改成：

```python
RUN_SIMULATION = True
```

## 当前科学实现约定

第一版代码遵守 `cowithAI/python_rccn_project_architecture_and_pseudocode.md` 中已经确认的约定：

- cycle length sampling 参考 MATLAB `initJij.m`；
- 使用 sparse matrix 计算 `J @ spins + H`；
- 使用同步 spin update；
- 如果 `local_field == 0`，保留上一时刻 spin，并记录 zero-field count；
- magnetization 使用 cycle-averaged magnetization，对应 MATLAB `mag_B`；
- recovery time 定义为 stress removal 后第一次严格低于 baseline magnetization 的时间；
- 默认保存 release snapshot 和 early recovery snapshot，不保存完整 spin trajectory；
- 第一版 clustering 使用 PCA 后接 k-means，默认 `K = 3`。


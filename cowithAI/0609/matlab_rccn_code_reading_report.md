# MATLAB RCCN / Spin-Glass 原始代码阅读报告

来源代码目录：

```text
F:\aging_code\homework\q-bio_homework\qbio_final_project\Original_code_matlab
```

本报告只阅读 MATLAB 原始代码，不写 Python 实现。目标是为后续最小 Python 重构明确：主入口、模型参数、spin states、spin 更新规则、lag/recovery time、trajectory 保存情况，以及最小重构边界。

## 0. 原始代码整体地图

原始代码分成三层：

1. **运行模拟**
   - `runSimulationExperiments.m`
   - `initParams.m`
   - `initJij.m`
   - `genShiftMat.m`
   - `initSpins.m`
   - `dynamicExperiment.m`

2. **从 spin trajectory 计算 observable**
   - `getObservablesForMultipleTw.m`
   - `getObservables.m`

3. **用 magnetization 结果画图和计算 survival / recovery distribution**
   - `ShowSimulationData.m`
   - `getCDF.m`
   - `fitMagRise.m`
   - `fitMagRelaxB15.m`
   - `getMagRelax.m`
   - `survivalTheory.m`
   - `viridis.m`

对本项目最重要的科学主流程是：

```text
runSimulationExperiments.m
    -> initParams.m
    -> initJij.m
    -> dynamicExperiment.m
        -> initSpins.m
        -> spins = sign(J_ij * spins + H)
        -> save spins_hist

getObservablesForMultipleTw.m
    -> getObservables.m
        -> load spins_hist
        -> convert true/false back to +1/-1
        -> compute cycle-averaged magnetization mag_B

ShowSimulationData.m
    -> getCDF.m
        -> find first time after stress removal when magnetization returns below baseline
```

## 1. 哪个 MATLAB 文件是主入口

**主模拟入口是 `runSimulationExperiments.m`。**

证据：

- README 明确说 `RunSimulationExperiments.m` 是运行模拟的 main script。
- `runSimulationExperiments.m` 的开头注释写明：这个脚本启动一系列 simulation experiments。
- 它定义输出目录、waiting times、重复次数，然后调用 `initParams`、`initJij` 和 `dynamicExperiment`。

关键位置：

- `runSimulationExperiments.m:21` 定义 `dest_folder`
- `runSimulationExperiments.m:25` 定义 waiting times：`tw`
- `runSimulationExperiments.m:26` 定义 `run_num`
- `runSimulationExperiments.m:33` 调用 `initParams`
- `runSimulationExperiments.m:57` 调用 `initJij`
- `runSimulationExperiments.m:64` 调用 `dynamicExperiment`

需要区分：

- `runSimulationExperiments.m` 是**生成 spin dynamics 数据**的主入口。
- `getObservablesForMultipleTw.m` 是**把 spin history 转成 magnetization**的后处理入口。
- `ShowSimulationData.m` 是**画 survival curve / mean magnetization / theory fit**的分析入口。

如果只能回答一个主入口，应回答：

```text
runSimulationExperiments.m
```

## 2. 哪些参数控制模型

### 2.1 模拟批次和实验协议参数

这些参数主要在 `runSimulationExperiments.m`：

| 参数 | 位置 | 含义 |
|---|---:|---|
| `dest_folder` | `runSimulationExperiments.m:21` | 保存模拟结果的位置 |
| `different_initial_conditions` | `runSimulationExperiments.m:22` | 控制 ensemble 来自不同初始 spin，还是不同网络结构 |
| `tw` | `runSimulationExperiments.m:25` | 外部 stress field 持续时间，也就是 waiting time |
| `run_num` | `runSimulationExperiments.m:26` | 每个 `tw` 下的模拟重复数；README 解释为 cells / realizations |

默认值：

```matlab
dest_folder = 'Experiments/Spins/Exp1';
different_initial_conditions = false;
tw = [20,40,80,160,320,640,1280,3000];
run_num = 900;
```

### 2.2 核心模型参数

这些参数在 `initParams.m`：

| 参数 | 默认值 | 含义 |
|---|---:|---|
| `num_spins` | `2^14` | spin 总数 |
| `exp_times` | `[2000, 3000, 9000]` | 三阶段模拟时长：预平衡、stress、恢复 |
| `gamma` | `1.5` | inter-cycle coupling strength 的尺度 |
| `H` | `[0, 0.8, 0]` | 三阶段外部磁场 / stress field |

关键位置：

- `initParams.m:9`：`num_spins = 2^14`
- `initParams.m:10`：`exp_times = [2000, 3000, 9000]`
- `initParams.m:11`：`gamma = 1.5`
- `initParams.m:12`：`H = [0, 0.8, 0]`

注意：`runSimulationExperiments.m` 会在每个 `tw` 循环中用 `exp_times(2)=tw(i)` 覆盖第二阶段长度。因此 `initParams.m` 里的 `3000` 是默认 stress 时长，但实际批量模拟由 `tw` 数组逐个替换。

### 2.3 网络结构参数

这些参数和规则在 `initJij.m`：

| 参数 / 变量 | 含义 |
|---|---|
| `block_size` | 每个 cycle 的长度 |
| `blocks_locations` | 每个 cycle 的起始 spin index |
| `blocks_sizes` | 所有 cycle 的长度列表 |
| `coupling_idx` | 每个 cycle 中被选出来参与 inter-cycle coupling 的 spin |
| `J_ij` | spin interaction matrix，同时包含 cycle 内 shift 和 cycle 间随机耦合 |
| `JInfo` | 每个 spin 所属 cycle 的起点和长度 |

核心规则：

- cycle length 由 `block_size = floor(1/(rand()^(1/0.5)))` 抽样。
- 如果 `block_size > 2500`，重新抽样。
- cycle 内部用 `genShiftMat(block_size)` 生成 cyclic permutation / shift matrix。
- cycle 间耦合在 `coupling_idx` 对应的行列上生成随机正态耦合。
- inter-cycle coupling 大小由 `gamma/sqrt(numel(blocks_sizes))` 缩放。

关键位置：

- `initJij.m:31`：抽样 `block_size`
- `initJij.m:33-34`：限制最大 cycle length 为 2500
- `initJij.m:48-53`：选择 `coupling_idx`
- `initJij.m:64`：生成 cycle 间随机耦合
- `initJij.m:72`：记录 `JInfo`
- `initJij.m:73`：写入 cycle 内 shift matrix

### 2.4 后处理和理论曲线参数

这些不直接控制原始 spin dynamics，但控制分析图和理论拟合：

- `getObservablesForMultipleTw.m`
  - `Tw`
  - `exp_num`
  - `dist_file_prefix`
  - `spins_hist_file_prefix`
  - `JInfo_file_prefix`
  - `exp_times`
  - `win`

- `ShowSimulationData.m`
  - `action_id`
  - `data_folder`
  - `Tws`
  - `init_time`
  - `lmin`
  - `lmax`
  - `relaxation_time`
  - `mean_std`
  - `tau0`
  - `sat_mag`
  - `tau1`
  - `tauPlus`

这些参数用于 observable / plotting，不是 spin 更新方程本身。

## 3. 哪些变量是 spin states

原始代码中的 spin states 主要有两个层级。

### 3.1 当前时刻 spin vector

当前状态变量是：

```matlab
spins
```

它在 `initSpins.m` 中初始化：

```matlab
spins = sign(0.5 - rand(num_spins,1,'single','gpuArray'));
```

含义：

- `spins` 是长度为 `num_spins` 的列向量。
- 每个元素是一个 spin state。
- 取值为 `-1` 或 `+1`。
- 它是动态更新时真正被代入 `J_ij * spins` 的状态向量。

关键位置：

- `initSpins.m:15`
- `dynamicExperiment.m:23-24`

### 3.2 全时间 spin trajectory

保存全时间历史的变量是：

```matlab
spins_hist
```

它在 `initSpins.m` 中创建：

```matlab
spins_hist = false(num_spins,exp_len,'gpuArray');
```

在 `dynamicExperiment.m` 的每个 time step 保存：

```matlab
spins_hist(:,spins_hist_idx) = spins>0;
```

含义：

- `spins_hist` 是 `num_spins x total_time` 矩阵。
- 行是 spin index。
- 列是 time step。
- 为了节省空间，它不是直接保存 `-1/+1`，而是保存 Boolean：
  - `true` 表示 `+1`
  - `false` 表示 `-1`

在 `getObservables.m` 中读取后转换回数值 spin：

```matlab
spins_hist = gpuArray(spins_hist)*2-1;
```

关键位置：

- `initSpins.m:17`
- `dynamicExperiment.m:17`
- `dynamicExperiment.m:31`
- `getObservables.m:32`
- `getObservables.m:35`

### 3.3 不是原始 spin state，但由 spin state 聚合而来

以下变量不是单个 spin state，而是按 cycle 聚合后的状态 / observable：

| 变量 | 含义 |
|---|---|
| `cycles_hist_A` | 每个 cycle 的 magnetization，按 `sqrt(length)` 归一化 |
| `cycles_hist_B` | 每个 cycle 的 magnetization，按 cycle length 归一化 |
| `cycles_hist_C` | 每个 cycle 的 raw sum |
| `mag_A` | 所有 cycles 的总 magnetization，A 归一化 |
| `mag_B` | 所有 cycles 的总 magnetization，B 归一化 |
| `mag_C` | 所有 spins 的简单平均型 magnetization |

对你的项目，最接近 RCCN 原始定义的全局 magnetization 是 `mag_B`，因为它先对每个 cycle 按长度平均，再对 cycles 平均。`getObservablesForMultipleTw.m` 中调用：

```matlab
[~,~,~,~,mag,~] = getObservables(...)
```

这里接收的是第 5 个输出，也就是 `mag_B`。

## 4. 哪个函数更新 spin states

更新 spin states 的函数是：

```text
dynamicExperiment.m
```

具体更新发生在：

```matlab
loc_field = J_ij * spins + H(exp_part) + 0*(rand(num_spins,1,'single','gpuArray')-0.5);
spins = sign(loc_field);
```

关键位置：

- `dynamicExperiment.m:23` 计算 local field
- `dynamicExperiment.m:24` 用 `sign(loc_field)` 更新 `spins`

科学含义：

```text
每个 spin 在每个 time step 同步更新。
它的新状态由三部分决定：
1. 网络输入：J_ij * spins
2. 当前实验阶段的外部场：H(exp_part)
3. 噪声项：代码里乘以 0，所以默认没有噪声
```

注意：cycle 内 shift dynamics 并没有单独写在 `dynamicExperiment.m` 里，而是提前编码进 `J_ij`：

- `initJij.m` 在每个 cycle block 内写入 `genShiftMat(block_size)`。
- `genShiftMat.m` 返回 cyclic permutation matrix。
- 所以 `J_ij * spins` 同时实现了 cycle 内 shift 和 cycle 间耦合。

## 5. 哪个变量对应 lag / recovery time

原始代码中没有一个显式命名为 `lag_time` 或 `recovery_time` 的持久变量。

真正对应单次模拟 recovery / lag time 的变量是 `getCDF.m` 里的局部变量：

```matlab
i = find(mRelaxation<0,1);
```

含义：

- `mBase = mean(m(init_time-1000:init_time))` 是 stress 前的 baseline magnetization。
- `mRelaxation = mag(curr_exp,1+init_time+Tw:end)` 是 stress 关闭后的 magnetization。
- `mRelaxation = mRelaxation - mBase` 把恢复曲线减去 baseline。
- `i = find(mRelaxation<0,1)` 找到 stress 关闭后第一次回到 baseline 以下的时间点。

因此：

```text
单个 run 的 lag / recovery time ≈ getCDF.m 中的 i
```

更明确地说：

```text
tau = first index after stress removal where mag(t) - mBase < 0
```

关键位置：

- `getCDF.m:8`：计算 baseline `mBase`
- `getCDF.m:9`：截取 stress 关闭后的 `mRelaxation`
- `getCDF.m:10`：减去 baseline
- `getCDF.m:11`：第一次 crossing index `i`
- `getCDF.m:15`：把 `i` 加入 `pdf`
- `getCDF.m:18-19`：从 `pdf` 生成 `cdf`

注意区分：

- `Tw` 是 waiting time / stress duration，不是 recovery time。
- `i` 是每个 run 的 first-passage recovery index。
- `cdf` 是 recovery time 的累计分布。
- `survival = 1 - cdf` 是尚未恢复的比例。
- `tau0`、`tau1`、`tauPlus` 是理论拟合 / 理论曲线参数，不是每个模拟 cell 的 recovery time。

## 6. 原始代码是否已经保存 trajectory

**是，原始模拟代码已经保存了 trajectory。**

保存的变量是：

```matlab
spins_hist
```

保存位置由 `runSimulationExperiments.m` 的 `dest_folder` 和 `dynamicExperiment.m` 的 `prefix_str` 决定。默认会形成类似：

```text
Experiments/Spins/Exp1/T20R1.mat
Experiments/Spins/Exp1/T20R2.mat
...
Experiments/Spins/Exp1/T3000R900.mat
```

每个 `.mat` 文件里保存：

```matlab
spins_hist
```

并且如果 `different_initial_conditions = false`，每个 run / Tw 还会保存对应的：

```matlab
JInfo
```

保存逻辑：

- `dynamicExperiment.m:17` 每步保存当前 `spins`
- `dynamicExperiment.m:31` 保存 `spins_hist`
- `runSimulationExperiments.m:60` 保存每次网络结构的 `JInfo`

但是需要特别注意：

1. `spins_hist` 是完整 spin trajectory，不只是 snapshot。
2. `spins_hist` 用 Boolean 压缩保存，不是直接的 `-1/+1`。
3. `getObservablesForMultipleTw.m` 后处理时只保存 `mag`，不会继续保存 `spins_hist`。
4. 仓库里的 `NumericData/T*.mat` 看起来是文章图用的 magnetization 数据，通常只包含 `mag`，不等价于可直接做 PCA / clustering 的 spin-state matrix。

所以结论是：

```text
原始模拟代码会保存 trajectory；
但现成 NumericData 主要保存 magnetization，不一定包含原始 spin trajectory。
如果要做 spin-state clustering，最好从 Experiments/Spins 里的 spins_hist 提取 snapshot；
如果该目录没有实际运行结果，则需要重新运行 MATLAB 模拟或重构后重新生成。
```

## 7. Python 最小重构计划

这里不给 Python 代码，只给最小、可验证、不过度工程化的重构计划。

### 7.1 重构目标

最小 Python 版本只需要完成四件事：

1. 复现 RCCN spin dynamics 的核心行为。
2. 保存 release-time spin snapshots，用于 PCA / clustering。
3. 计算 magnetization 和 lag / recovery time。
4. 输出可追踪的 metadata，便于把 spin clusters 和 recovery time 关联起来。

不要一开始重构成大包、复杂类系统或通用模拟框架。

### 7.2 最小函数结构

推荐函数层级：

```text
make_params
build_rccn_network
initialize_spins
run_one_simulation
compute_cycle_averaged_magnetization
compute_recovery_time
run_batch
save_outputs
```

每个函数的科学职责：

| 函数 | 作用 |
|---|---|
| `make_params` | 显式保存 `num_spins`, `init_time`, `Tw`, `relax_time`, `gamma`, `H` |
| `build_rccn_network` | 复现 `initJij.m` 的 cycle length、`JInfo`、cycle shift、inter-cycle coupling |
| `initialize_spins` | 复现 `initSpins.m` 的随机 `-1/+1` 初始状态 |
| `run_one_simulation` | 复现 `dynamicExperiment.m` 的同步更新 |
| `compute_cycle_averaged_magnetization` | 复现 `getObservables.m` 中的 `mag_B` |
| `compute_recovery_time` | 复现 `getCDF.m` 的 first crossing 定义 |
| `run_batch` | 对多个 `Tw` 和多个 run 循环 |
| `save_outputs` | 保存 snapshots、metadata、magnetization、参数 |

### 7.3 必须保留的行为

最小重构必须保留这些原始行为：

1. `num_spins = 2^14`，除非为了 toy test 临时改小。
2. 三阶段实验协议：预平衡、stress、恢复。
3. `H = [0, 0.8, 0]` 的 stress protocol。
4. `Tw` 控制第二阶段时长。
5. 同步更新：

```text
spins(t+1) = sign(J_ij * spins(t) + H)
```

6. 噪声默认为 0。
7. cycle 内 shift 通过 block permutation matrix 或等价逻辑实现。
8. cycle-averaged magnetization 使用 `mag_B` 的定义。
9. recovery time 使用 stress 关闭后第一次回到 baseline 以下的 first-passage index。

### 7.4 为本项目新增的最小输出

原始代码已经保存全 trajectory，但为了本项目的 PCA / clustering，Python 最小重构建议直接保存更清楚的分析矩阵：

```text
X_spin_release
```

含义：

- 行：simulation run / simulated cell
- 列：spin index
- 值：`-1/+1`
- 时间点：`init_time + Tw`，即 stress 关闭瞬间

推荐同时保存 metadata：

| 字段 | 含义 |
|---|---|
| `run_id` | 模拟编号 |
| `Tw` | waiting time / stress duration |
| `recovery_time` | first-passage lag time |
| `snapshot_time` | snapshot 对应的绝对 time index |
| `num_spins` | spin 总数 |
| `gamma` | coupling strength |
| `H_stress` | stress field 强度 |
| `network_id` | 网络结构编号 |
| `different_initial_conditions` | ensemble 类型 |

可选保存：

```text
X_spin_early_recovery
```

例如：

```text
snapshot_time = init_time + Tw + delta_t
```

### 7.5 不建议第一版做的事

第一版不建议：

1. 不要直接重构全部 plotting / fitting 脚本。
2. 不要先实现 PETRI-seq 比较。
3. 不要写复杂配置系统。
4. 不要写复杂异常类。
5. 不要为所有可能参数做通用化。
6. 不要默认保存 900 个 run 的完整 full trajectory，除非验证确实需要。

原因：

- `spins_hist` 尺寸约为 `num_spins x total_time`。
- 默认 `num_spins = 16384`，`total_time = 2000 + Tw + 9000`。
- 对 900 runs 和多个 `Tw` 保存完整 trajectory 会非常大。
- 对 clustering 来说，release snapshot 和 metadata 通常更直接。

### 7.6 建议的验证顺序

最小重构应先验证，再扩展：

1. **toy network one-step test**
   - 用很小的 `num_spins` 和固定 `J_ij`。
   - 检查一次更新是否等于 MATLAB 逻辑。

2. **network structure check**
   - 检查 cycle lengths 是否覆盖所有 spins。
   - 检查 `JInfo` 是否能恢复每个 spin 的 cycle 起点和长度。
   - 检查 inter-cycle coupling 缩放是否使用 `gamma/sqrt(num_cycles)`。

3. **magnetization check**
   - 对同一个 `spins_hist`，Python 计算出的 cycle-averaged `mag_B` 应接近 MATLAB `getObservables.m`。

4. **recovery-time check**
   - 对同一个 `mag`，Python 计算出的 first crossing 应对应 MATLAB `getCDF.m` 里的 `i`。

5. **statistical behavior check**
   - 多个 `Tw` 下 recovery-time distribution 应表现出与 `NumericData` 类似的趋势。

## 8. 给后续重构者的简短指令

后续如果开始写 Python，核心原则是：

```text
先复现动态方程和 recovery-time 定义，再做 clustering。
```

必须优先读懂和对齐：

- `runSimulationExperiments.m`
- `initParams.m`
- `initJij.m`
- `initSpins.m`
- `dynamicExperiment.m`
- `getObservables.m`
- `getCDF.m`

第一版最小输出应是：

```text
1. release spin-state matrix
2. metadata table with Tw and recovery_time
3. optional magnetization curves
4. validation plots against original NumericData
```

一句话总结：

```text
原始 MATLAB 已经能生成 full spin trajectory；本项目最小重构的关键不是重新发明模型，而是把 release spin states、Tw、recovery time 和 model parameters 以清楚、可聚类、可验证的格式保存出来。
```

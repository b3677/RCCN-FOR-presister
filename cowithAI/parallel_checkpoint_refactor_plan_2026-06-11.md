# RCCN final simulation CPU parallel + per-Tw checkpoint refactor plan

## 1. 当前目标

这次重构只针对 `final` simulation 的运行效率和抗中断能力，不改变 RCCN 模型本身、不改变 downstream analysis/figures 的输入文件名和字段含义。

当前机器配置：

- `NumberOfCores = 8`
- `NumberOfLogicalProcessors = 16`

目标：

1. 把 5 个 waiting time (`Tw = 0, 195, 488, 1346, 1500`) 的模拟结果分开保存，也就是每完成一个 `Tw` 就落盘一次。
2. 把同一个 `Tw` 下的 2000 个 independent cell runs 用 CPU 多进程并行。
3. 如果 Windows Update、断电、手动停止等外部原因打断，重跑时可以跳过已经完成的 `Tw`。
4. 最后仍然生成现在分析脚本需要的总输出：
   - `metadata.csv`
   - `magnetization.csv`
   - `spin_release.npy`
   - `spin_early_recovery.npy`
   - `selected_spin_snapshots.npy`
   - `snapshot_metadata.csv`
   - `cycle_group_features.csv`
   - `params.json`

## 2. 科学和计算结构

当前科学主流程是：

1. 对每个 `Tw`，模拟 `n_runs = 2000` 个 cell。
2. 每个 cell 有自己的随机 RCCN network 和随机初始 spins。
3. 每个 cell 按 `init -> stress waiting -> relax` 的 protocol 更新 spins。
4. 记录 magnetization、release snapshot、early recovery snapshot、selected recovery snapshots、cycle group features。
5. 后续 PCA/UMAP/clustering/figures 基于这些模拟输出。

这说明：

- 不同 `run_id` 的 cell simulation 是相互独立的，可以并行。
- 同一个 cell 内部的 time steps 不能简单并行，因为 `spins[t+1]` 依赖 `spins[t]`。
- GPU 改造不是本轮目标；本轮只做 CPU 多进程和 checkpoint。

## 3. 必须保持不变的行为

保持不变：

- `run_one_cell()` 的科学含义。
- `run_one_protocol()` 中的 spin update 规则。
- `build_rccn_network()` 的网络生成规则。
- recovery time、baseline magnetization、cycle group feature 的定义。
- `output/result611/final_simulation` 下最终总输出的文件名和表格字段。
- `run_final_state_analysis.py` 和 `make_final_project_figures.py` 的读取方式。

可以变化：

- 模拟运行顺序可以从串行变成并行。
- 中间会多出 checkpoint 文件夹。
- 每个 run 的随机数来源会从一个共享 `rng` 串行推进，改为每个 `run_id` 一个确定性 seed。

重要说明：

并行版可以保证“同一参数 + 同一 base seed -> 可重复”，也可以保证不同 worker 数量下结果一致。但是它通常不能保证和旧串行版本逐位相同，因为旧版本用一个 `rng` 依次推进，而每个 run 消耗的随机数数量会随 network 采样中的 while loop 变化。这个变化不改变模型设定，但会改变具体随机样本。

## 4. 输出目录设计

保留最终总输出目录：

```text
output/result611/final_simulation/
```

新增每个 `Tw` 的 checkpoint 目录：

```text
output/result611/final_simulation/checkpoints/
    Tw_0/
        metadata.csv
        magnetization.csv
        spin_release.npy
        spin_early_recovery.npy
        selected_spin_snapshots.npy
        snapshot_metadata.csv
        cycle_group_features.csv
        done.json
    Tw_195/
        ...
    Tw_488/
        ...
    Tw_1346/
        ...
    Tw_1500/
        ...
```

`done.json` 建议包含：

```text
Tw
n_runs
num_spins
random_seed
worker_count
finished_at
output_files
```

用途：

- 有 `done.json` 且基本参数匹配时，重跑可以跳过这个 `Tw`。
- 如果某个 `Tw` 没有 `done.json`，说明可能是半成品，默认重新跑这个 `Tw`。
- 最终合并时只读取带 `done.json` 的完整 checkpoint。

## 5. 文件级修改计划

### 5.1 `src/rccn_persistence/simulation.py`

主要修改：

- 保留 `run_one_cell()`。
- 保留 `run_for_one_waiting_time()` 作为串行版本，便于 smoke/debug。
- 新增 worker 级函数，用于 Windows 多进程。
- 新增并行版本 `run_for_one_waiting_time_parallel()`。
- 新增 batch/checkpoint 版本 `run_batch_with_tw_checkpoints()`。
- 新增合并函数，把 5 个 `Tw` checkpoint 合并成原来的 `batch_result` 结构。

建议新增函数：

```text
make_run_seed(base_seed, Tw, run_id)
run_one_cell_from_seed(params, Tw, run_id, seed)
run_for_one_waiting_time_parallel(params, Tw, n_runs, run_id_start, workers)
merge_waiting_time_results(waiting_time_results)
run_batch_with_tw_checkpoints(params, checkpoint_dir, workers, resume=True)
```

不建议新增类，也不需要复杂调度框架。

### 5.2 `src/rccn_persistence/io_utils.py`

主要修改：

- 保留 `save_final_simulation_outputs()` 和 `load_final_simulation_outputs()`。
- 新增保存单个 `Tw` checkpoint 的函数。
- 新增读取单个 `Tw` checkpoint 的函数。
- 新增检查 checkpoint 是否完整的函数。

建议新增函数：

```text
save_waiting_time_checkpoint(result, checkpoint_root, Tw, params)
load_waiting_time_checkpoint(checkpoint_root, Tw)
is_waiting_time_checkpoint_complete(checkpoint_root, Tw, params)
```

注意：

- checkpoint 保存的字段应该和 `run_for_one_waiting_time()` 返回值一致。
- `done.json` 最后写入。这样如果中途崩掉，不会误判为完整。

### 5.3 `scripts/run_final_rccn_simulation.py`

主要修改：

- 增加 CLI 参数：
  - `--workers`
  - `--no-resume`
  - `--serial`
- 默认 final run 使用 checkpoint + parallel。
- smoke run 可以默认继续串行，避免小测试被多进程启动开销拖慢。
- 最后仍然调用 `save_final_simulation_outputs()` 保存总输出。

建议默认：

```text
workers = min(12, os.cpu_count() or 1)
```

理由：

- 你的电脑有 16 logical processors。
- 默认用 12 个 worker 可以显著加速，同时给系统、磁盘、IDE 留一点余量。
- 如果想压满，可以手动 `--workers 16`。

### 5.4 `scripts/run_overnight_final_pipeline.ps1`

可选修改：

- 增加一个参数把 workers 传给 Python 脚本，例如 `-Workers 12`。
- 在 `Invoke-LoggedStep "full_final_simulation"` 的 argument list 中加：

```text
--workers 12
```

也可以先不改 PowerShell，直接在 Python 脚本中设置默认 worker 数。

### 5.5 `README.md`

建议补充一小段运行方式：

```text
.\scripts\run_result611_pipeline.ps1
```

或直接：

```text
F:\conda_envs\e_coli_rpy2_py311\python.exe scripts\run_final_rccn_simulation.py --preset final --workers 12
```

说明 checkpoint 目录和 resume 行为。

## 6. 函数级伪代码

### 6.1 `make_run_seed(base_seed, Tw, run_id)`

作用：

为每个 cell run 生成稳定 seed，使并行运行不依赖 worker 调度顺序。

伪代码：

```text
function make_run_seed(base_seed, Tw, run_id):
    1. 用 base_seed, Tw, run_id 组成确定性输入
    2. 通过 numpy SeedSequence 生成一个 uint32 seed
    3. 返回这个 seed
```

注意：

实际代码中可以用 `np.random.SeedSequence([base_seed, int(Tw), int(run_id)])`。

### 6.2 `run_one_cell_from_seed(params, Tw, run_id, seed)`

作用：

多进程 worker 的最小任务单元。每个 worker 独立创建 rng，然后调用现有 `run_one_cell()`。

伪代码：

```text
function run_one_cell_from_seed(params, Tw, run_id, seed):
    1. rng = np.random.default_rng(seed)
    2. result = run_one_cell(params, Tw, run_id, rng)
    3. 返回 result
```

保留点：

- `run_one_cell()` 内部科学逻辑不改。
- network 仍然每个 cell 重新生成。

### 6.3 `run_for_one_waiting_time_parallel(params, Tw, n_runs, run_id_start, workers)`

作用：

并行跑完一个 `Tw` 下的所有 runs。

伪代码：

```text
function run_for_one_waiting_time_parallel(params, Tw, n_runs, run_id_start, workers):
    1. 建立 task list:
        对 local_run in 0..n_runs-1:
            run_id = run_id_start + local_run
            seed = make_run_seed(params["random_seed"], Tw, run_id)
            task = (params, Tw, run_id, seed)
    2. 用 ProcessPoolExecutor(max_workers=workers) 提交所有 task
    3. 每完成一个 task:
        收集 result
        打印进度，例如 [simulate] Tw=195, done=123/2000
    4. 按 run_id 排序 result，避免并行完成顺序影响输出顺序
    5. 组装成和 `run_for_one_waiting_time()` 一样的 dict:
        metadata
        magnetization
        spin_release
        spin_early_recovery
        selected_spin_snapshots
        snapshot_metadata
        cycle_group_features
    6. 返回这个 dict
```

Windows 注意：

- worker 函数必须定义在模块顶层，不能定义在另一个函数内部。
- `scripts/run_final_rccn_simulation.py` 已经有 `if __name__ == "__main__": main()`，适合 multiprocessing。

### 6.4 `save_waiting_time_checkpoint(result, checkpoint_root, Tw, params)`

作用：

每完成一个 `Tw` 就保存一次，避免外部中断导致所有进度丢失。

伪代码：

```text
function save_waiting_time_checkpoint(result, checkpoint_root, Tw, params):
    1. tw_dir = checkpoint_root / f"Tw_{Tw}"
    2. 创建 tw_dir
    3. 保存 result 中的 csv 和 npy 文件
    4. 写一个临时 done.tmp.json
    5. 将 done.tmp.json rename 成 done.json
```

关键原则：

- `done.json` 最后写。
- 如果保存中途失败，不会出现完整标记。

### 6.5 `is_waiting_time_checkpoint_complete(checkpoint_root, Tw, params)`

作用：

判断某个 `Tw` 是否可以复用。

伪代码：

```text
function is_waiting_time_checkpoint_complete(checkpoint_root, Tw, params):
    1. 检查 Tw_xxx/done.json 是否存在
    2. 检查 metadata.csv 等必需文件是否存在
    3. 读取 done.json
    4. 比较 Tw, n_runs, num_spins, random_seed, selected_recovery_times 等关键参数
    5. 如果全部匹配，返回 True
    6. 否则返回 False
```

参数匹配建议：

- 必须匹配：
  - `Tw`
  - `n_runs`
  - `num_spins`
  - `init_time`
  - `relax_time`
  - `gamma`
  - `H_init`
  - `H_stress`
  - `H_relax`
  - `max_cycle_length`
  - `selected_recovery_times`
  - `random_seed`

### 6.6 `run_batch_with_tw_checkpoints(params, checkpoint_root, workers, resume=True)`

作用：

外层 batch 函数。按 `Tw` 顺序处理，每完成一个 `Tw` 保存 checkpoint，最后合并。

伪代码：

```text
function run_batch_with_tw_checkpoints(params, checkpoint_root, workers, resume=True):
    1. waiting_time_results = []
    2. next_run_id = 0
    3. for Tw in params["waiting_times"]:
        a. 如果 resume=True 且 Tw checkpoint 完整:
            result = load_waiting_time_checkpoint(checkpoint_root, Tw)
            打印 [resume] loaded Tw=...
        b. 否则:
            result = run_for_one_waiting_time_parallel(
                params=params,
                Tw=Tw,
                n_runs=params["n_runs"],
                run_id_start=next_run_id,
                workers=workers,
            )
            save_waiting_time_checkpoint(result, checkpoint_root, Tw, params)
            打印 [checkpoint] saved Tw=...
        c. waiting_time_results.append(result)
        d. next_run_id += params["n_runs"]
    4. batch_result = merge_waiting_time_results(waiting_time_results)
    5. return batch_result
```

### 6.7 `merge_waiting_time_results(waiting_time_results)`

作用：

把 5 个 `Tw` checkpoint 重新合并成当前 downstream 代码需要的总结果。

伪代码：

```text
function merge_waiting_time_results(waiting_time_results):
    1. pd.concat 所有 metadata
    2. pd.concat 所有 magnetization
    3. np.vstack 所有 spin_release
    4. np.vstack 所有 spin_early_recovery
    5. np.vstack 所有 selected_spin_snapshots
    6. pd.concat 所有 snapshot_metadata
    7. pd.concat 所有 cycle_group_features
    8. 返回 batch_result dict
```

## 7. CLI 设计

建议 `scripts/run_final_rccn_simulation.py` 支持：

```text
--workers N
    使用 N 个 worker 进程。

--serial
    强制使用旧串行运行方式，便于 debug 或比较。

--no-resume
    不复用已有 checkpoint，重新跑所有 Tw。
```

推荐运行：

```text
python scripts/run_final_rccn_simulation.py --preset final --workers 12
```

保守运行：

```text
python scripts/run_final_rccn_simulation.py --preset final --workers 8
```

压满机器：

```text
python scripts/run_final_rccn_simulation.py --preset final --workers 16
```

## 8. 测试计划

### 8.1 语法和导入检查

```text
python scripts/check_final_pipeline_imports.py
```

### 8.2 smoke test

```text
python scripts/run_final_rccn_simulation.py --preset smoke --workers 2
python scripts/run_final_state_analysis.py
python scripts/make_final_project_figures.py
```

检查：

- smoke checkpoint 是否生成。
- 最终总输出是否仍能被 analysis 读取。
- figures 是否仍能生成。

### 8.3 小规模 final-like test

建议跑一个小但不是 smoke 的测试：

```text
python scripts/run_final_rccn_simulation.py --preset final --n-runs 20 --waiting-times 0 195 --workers 4
python scripts/run_final_state_analysis.py
```

检查：

- `Tw_0` 和 `Tw_195` checkpoint 是否生成。
- 重新运行同一命令时是否直接 resume。
- 删除某个 `Tw_xxx/done.json` 后是否只重跑该 `Tw`。

### 8.4 完整运行

```text
python scripts/run_final_rccn_simulation.py --preset final --workers 12
python scripts/run_final_state_analysis.py
python scripts/make_final_project_figures.py
```

预期：

- simulation 时间明显低于串行版。
- analysis 和 figures 时间基本不变。

## 9. 风险和需要确认的点

### 9.1 随机数逐位一致性

CPU 并行后，推荐每个 `run_id` 使用独立 seed。这样结果可复现，但一般不会和旧串行版本逐位一致。

判断：

- 如果你的要求是“统计含义不变、图像结论不变”，可以接受。
- 如果你的要求是“和旧版本完全同一个随机序列”，不建议并行，或者需要做更复杂的随机流预分配设计。

### 9.2 内存占用

每个 worker 同时持有一个 network 和 trajectory 中间数据。16 个 worker 可能会占用较多内存。

建议：

- 默认 `--workers 12`。
- 如果系统卡顿或内存吃紧，改成 `--workers 8`。

### 9.3 checkpoint 是否按 run 分得更细

本计划按 `Tw` 保存，共 5 份。优点是结构简单，认知负担低。

缺点是如果某个 `Tw` 跑到 1900/2000 时中断，还是要重跑这个 `Tw`。

更细方案是每 100 runs 保存一个 chunk，但会让保存、合并、resume 逻辑复杂不少。本轮不建议，除非后续仍然频繁被打断。

## 10. 本轮不做的事情

不做：

- GPU/CUDA 改写。
- 改 spin dynamics 数学逻辑。
- 复用同一个 network 来提速。
- 增加复杂 logging 框架。
- 增加类封装或配置系统。
- 改 analysis/figures 的输入 schema。

原因：

这些要么会改变科学含义，要么会明显增加调试成本，不适合 final project 当前阶段。

## 11. 给下一步代码修改的执行说明

如果确认执行，实现顺序建议是：

1. 在 `io_utils.py` 增加 checkpoint 保存/读取函数。
2. 在 `simulation.py` 增加并行 worker、并行 `Tw` runner、checkpoint batch runner、merge 函数。
3. 在 `run_final_rccn_simulation.py` 增加 CLI 参数，并接入新 batch runner。
4. 跑 smoke test。
5. 跑小规模 final-like test。
6. 确认 resume 行为。
7. 再跑完整 final。

代码修改时优先保持函数式、直接、可读。不要引入复杂类，也不要在核心科学计算里包宽泛 `try/except`。

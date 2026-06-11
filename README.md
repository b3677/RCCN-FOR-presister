# RCCN-FOR-presister

鏈」鐩槸涓€涓敤 Python 澶嶇幇鍜屾墿灞?RCCN / spin-glass 妯″瀷鐨勫皬鍨嬬鐮斾唬鐮佸簱锛岀敤浜庣爺绌舵姉鐢熺礌 persistence 涓?aging-dependent cell-state heterogeneity銆?
绗竴鐗堜唬鐮佺殑鐩爣涓嶆槸鍋氬鏉傝蒋浠舵鏋讹紝鑰屾槸褰㈡垚涓€鏉″彲妫€鏌ャ€佸彲淇敼銆佸彲澶嶇幇鐨勭鐮斿垎鏋愭祦绋嬶細

1. 鏋勫缓 randomly connected cycles network锛?2. 妯℃嫙 initialization銆乻tress銆乺elaxation 涓夐樁娈?spin dynamics锛?3. 淇濆瓨 stress release 鏃跺埢鍜?early recovery 鏃跺埢鐨?spin-state snapshots锛?4. 璁＄畻 cycle-averaged magnetization 鍜?recovery / lag time锛?5. 瀵?release spin states 鍋?PCA 鍜?k-means clustering锛?6. 杈撳嚭 summary tables 鍜?project figures銆?
## 椤圭洰缁撴瀯

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

## 鍏抽敭鏂囦欢璇存槑

### 绉戝璁捐鏂囨。

- `cowithAI/spin_glass_final_project_description.md`锛氶」鐩瀛﹁儗鏅拰鐮旂┒闂銆?- `cowithAI/matlab_rccn_code_reading_report.md`锛氬師濮?MATLAB 浠ｇ爜闃呰璁板綍銆?- `cowithAI/python_rccn_project_architecture_and_pseudocode.md`锛歅ython 绗竴鐗堟灦鏋勫拰鍑芥暟绾т吉浠ｇ爜銆?
### 鏍稿績 Python 妯″潡

- `src/rccn_persistence/config.py`锛氶粯璁ゅ弬鏁般€乨ebug 鍙傛暟銆佽緭鍑鸿矾寰勩€?- `src/rccn_persistence/network.py`锛歊CCN 缃戠粶鏋勫缓锛屽寘鎷?cycle length銆乧ycle start銆乧oupling index 鍜?sparse interaction matrix `J`銆?- `src/rccn_persistence/dynamics.py`锛歴pin 鍒濆鍖栥€佸悓姝ユ洿鏂拌鍒欍€乺elease / early recovery snapshot 淇濆瓨銆?- `src/rccn_persistence/observables.py`锛歝ycle-averaged magnetization銆乺ecovery time銆丆DF銆乻urvival curve銆?- `src/rccn_persistence/simulation.py`锛氬崟涓?simulated cell銆佸崟涓?`T_w`銆佹暣鎵?`T_w` 鐨勬ā鎷熸祦绋嬨€?- `src/rccn_persistence/io_utils.py`锛氫繚瀛樺拰璇诲彇妯℃嫙杈撳嚭銆?- `src/rccn_persistence/spin_analysis.py`锛歳elease spin matrix 鐨?PCA 鍜?k-means clustering銆?- `src/rccn_persistence/plotting.py`锛氶」鐩浘鍍忕粯鍒跺嚱鏁般€?
### 鑴氭湰鍏ュ彛

- `scripts/run_rccn_simulation.py`锛氳繍琛屾ā鎷熷苟淇濆瓨缁撴灉銆?- `scripts/run_spin_clustering.py`锛氳鍙栨ā鎷熺粨鏋滐紝杩愯 PCA / clustering锛屽苟淇濆瓨琛ㄦ牸銆?- `scripts/make_project_figures.py`锛氳鍙栧凡鏈夎緭鍑哄苟鐢熸垚椤圭洰鍥惧儚銆?
## 鍏抽敭鍙傛暟鍦ㄥ摢閲?
涓昏鍙傛暟闆嗕腑鍦細

```text
src/rccn_persistence/config.py
```

鍏朵腑锛?
- `make_default_params()`锛氶粯璁ょ瀛﹁繍琛屽弬鏁般€?- `make_debug_params()`锛氬揩閫熸鏌?pipeline 鐨勫皬瑙勬ā鍙傛暟銆?- `make_output_paths(project_root)`锛氱粺涓€瀹氫箟杈撳嚭璺緞銆?
閲嶈鍙傛暟濡備笅锛?
| 鍙傛暟 | 鍚箟 | 榛樿鍊?|
|---|---|---:|
| `num_spins` | 姣忎釜 RCCN 缃戠粶鐨?spin 鏁伴噺 | `2**14` |
| `init_time` | stress 鍓嶇殑鍒濆鍖?/ relaxation 鏃堕棿 | `2000` |
| `relax_time` | stress removal 鍚庣殑 relaxation 鏃堕棿 | `9000` |
| `waiting_times` | stress 鎸佺画鏃堕棿 `T_w` | `[20, 40, 80, 160, 320, 640, 1280, 3000]` |
| `gamma` | cycle 闂撮殢鏈鸿€﹀悎寮哄害 | `1.5` |
| `H_init` | 鍒濆鍖栭樁娈靛鍦?| `0.0` |
| `H_stress` | stress 闃舵澶栧満 | `0.8` |
| `H_relax` | stress removal 鍚庡鍦?| `0.0` |
| `n_runs` | 姣忎釜 `T_w` 涓?simulated cells 鏁伴噺 | `20` |
| `max_cycle_length` | 鏈€澶?cycle length | `2500` |
| `early_recovery_delta` | stress removal 鍚庡涔呬繚瀛?early snapshot | `100` |
| `baseline_window` | stress 鍓嶇敤浜庝及璁?baseline magnetization 鐨勭獥鍙?| `1000` |
| `pca_components` | PCA 淇濈暀缁村害 | `10` |con
| `n_clusters` | k-means cluster 鏁伴噺 | `3` |
| `random_seed` | 闅忔満绉嶅瓙 | `1` |

## 杈撳嚭璺緞鍜屾枃浠?
杈撳嚭璺緞鐢?`make_output_paths(project_root)` 缁熶竴瀹氫箟銆?
### 妯℃嫙杈撳嚭

淇濆瓨鍒帮細

```text
output/rccn_simulation/
```

鏂囦欢鍖呮嫭锛?
- `params.json`锛氭湰娆¤繍琛屼娇鐢ㄧ殑鍙傛暟銆?- `metadata.csv`锛氭瘡涓?simulated cell 涓€琛岋紝鍖呭惈 `run_id`銆乣Tw`銆乣recovery_time`銆乣recovered`銆乻napshot 鏃堕棿鍜?`zero_field_count`銆?- `magnetization.csv`锛氶暱琛ㄦ牸鏍煎紡鐨?magnetization time series锛屽寘鍚?`run_id`銆乣Tw`銆乣time`銆乣magnetization`銆?- `spin_release.npy`锛歴tress removal 鏃跺埢鐨?spin-state matrix锛屽舰鐘朵负 `(n_cells, num_spins)`銆?- `spin_early_recovery.npy`锛歴tress removal 鍚?`early_recovery_delta` steps 鐨?spin-state matrix銆?
### 鑱氱被杈撳嚭

淇濆瓨鍒帮細

```text
output/spin_clustering/
```

鏂囦欢鍖呮嫭锛?
- `pca_scores.csv`锛氭瘡涓?simulated cell 鐨?PCA 鍧愭爣銆?- `pca_explained_variance.csv`锛氬悇 PC 鐨?explained variance ratio銆?- `cluster_labels.csv`锛氭瘡涓?simulated cell 鐨?k-means cluster label銆?- `cluster_occupancy_by_Tw.csv`锛氫笉鍚?`T_w` 涓?cluster 鍗犳瘮銆?- `recovery_time_by_cluster.csv`锛氫笉鍚?cluster 鐨?recovery time summary銆?
### 鍥惧儚杈撳嚭

淇濆瓨鍒帮細

```text
output/figures/
```

褰撳墠鍥惧儚鍖呮嫭锛?
- `fig1_recovery_survival_by_Tw.png`
- `fig2_spin_pca_by_Tw.png`
- `fig3_spin_pca_by_cluster.png`
- `fig4_spin_pca_by_recovery_time.png`
- `fig5_cluster_occupancy_by_Tw.png`

## 蹇€熻繍琛?
杩愯娴嬭瘯锛?
```powershell
python -m pytest tests
```

杩愯涓€涓潪甯稿皬鐨?smoke test锛?
```powershell
python scripts\run_rccn_simulation.py --preset debug --num-spins 64 --n-runs 2 --waiting-times 3 5 --init-time 20 --relax-time 120 --early-recovery-delta 10 --baseline-window 10
python scripts\run_spin_clustering.py
python scripts\make_project_figures.py
```

杩愯榛樿 debug pipeline锛?
```powershell
python scripts\run_rccn_simulation.py --preset debug
python scripts\run_spin_clustering.py
python scripts\make_project_figures.py
```

濡傛灉瑕佸仛鏇村ぇ鐨勭瀛﹁繍琛岋紝鍙互鐩存帴淇敼 `src/rccn_persistence/config.py`锛屾垨鑰呴€氳繃 `scripts/run_rccn_simulation.py` 鐨勫懡浠よ鍙傛暟瑕嗙洊鍏抽敭璁剧疆銆?
## Notebook 鍏ュ彛

鏂板 notebook锛?
```text
notebooks/01_run_rccn_pipeline_and_view_results.ipynb
```

瀹冪敤浜庯細

1. 瀵煎叆涓诲嚱鏁帮紱
2. 鏌ョ湅鍜屼慨鏀瑰叧閿弬鏁帮紱
3. 鍙€夎繍琛屾ā鎷燂紱
4. 璇诲彇 `output/rccn_simulation/` 缁撴灉锛?5. 灞曠ず `metadata`銆乣magnetization` 鍜?spin snapshot shape锛?6. 杩愯 PCA / clustering锛?7. 鐢诲嚭 magnetization銆丳CA 鍜?recovery survival 鐨勫揩閫熼瑙堝浘銆?
榛樿鎯呭喌涓嬶紝notebook 涓嶄細鑷姩鍚姩闀挎椂闂存ā鎷熴€傞渶瑕侀噸鏂拌窇妯℃嫙鏃讹紝鎶?notebook 涓殑锛?
```python
RUN_SIMULATION = False
```

鏀规垚锛?
```python
RUN_SIMULATION = True
```

## 褰撳墠绉戝瀹炵幇绾﹀畾

绗竴鐗堜唬鐮侀伒瀹?`cowithAI/python_rccn_project_architecture_and_pseudocode.md` 涓凡缁忕‘璁ょ殑绾﹀畾锛?
- cycle length sampling 鍙傝€?MATLAB `initJij.m`锛?- 浣跨敤 sparse matrix 璁＄畻 `J @ spins + H`锛?- 浣跨敤鍚屾 spin update锛?- 濡傛灉 `local_field == 0`锛屼繚鐣欎笂涓€鏃跺埢 spin锛屽苟璁板綍 zero-field count锛?- magnetization 浣跨敤 cycle-averaged magnetization锛屽搴?MATLAB `mag_B`锛?- recovery time 瀹氫箟涓?stress removal 鍚庣涓€娆′弗鏍间綆浜?baseline magnetization 鐨勬椂闂达紱
- 榛樿淇濆瓨 release snapshot 鍜?early recovery snapshot锛屼笉淇濆瓨瀹屾暣 spin trajectory锛?- 绗竴鐗?clustering 浣跨敤 PCA 鍚庢帴 k-means锛岄粯璁?`K = 3`銆?

## Final simulation checkpoint run

The final RCCN simulation can run one `Tw` block at a time with CPU workers and
resume from completed checkpoints:

```powershell
C:\work\env_rccn_stable\python.exe scripts\run_final_rccn_simulation.py --preset final --workers 4
```

Completed checkpoints are stored under:

```text
output/result611/final_simulation/checkpoints/Tw_<value>/
```

Each completed `Tw` directory has a `done.json` marker. Re-running the same
command reuses complete matching checkpoints; pass `--no-resume` to recompute all
`Tw` blocks. For debugging with the old serial path, pass `--serial`.

The overnight pipeline passes workers through as:

```powershell
.\scripts\run_overnight_final_pipeline.ps1 -Workers 4
```

## Project summary and final figures

### Purpose

This project reproduces and extends an RCCN / spin-glass model for bacterial
persistence and ageing-dependent cell-state heterogeneity. The main scientific
question is whether different stress waiting times (`Tw`) create different
spin-state landscapes, recovery-time distributions, and presister-like tail
populations.

The current final workflow simulates many independent RCCN cells across
`Tw = 0, 195, 488, 1346, 1500`, analyzes their recovery and spin-state
structure, and redraws the final project figures under:

```text
output/result611/final_figures/
```

### References and data sources

- Original RCCN / spin-glass model code: `Original_code_matlab/`
- Project design and code-reading notes: `cowithAI/`
- Paper/reference materials: `ori_paper/`
- Experimental source table used for tail-fraction matching:
  `data/sourcefig2.xlsx`

The Python implementation keeps the main RCCN assumptions from the MATLAB
reference: randomly connected cycles, synchronous spin updates, zero-field spin
retention, stress waiting followed by relaxation, and cycle-averaged
magnetization as the recovery observable.

### Implemented final workflow

The final pipeline currently implements:

- RCCN simulation for multiple waiting times (`Tw`) and many independent cells.
- Per-`Tw` checkpointing and resume for long final simulations.
- CPU multiprocessing across independent cell simulations within each `Tw`.
- Recovery-time and mean recovery dynamics summaries.
- Selected spin snapshots at recovery times
  `0, 250, 500, 1000, 2000, 4000`.
- Full sklearn PCA, UMAP, and KMeans clustering on selected spin-state snapshots.
- Presister-like state labeling by matching simulated tail fractions to the
  experimental `sourcefig2.xlsx` table.
- Cycle/loop group feature summaries for short, medium, and long cycles.
- Final figure generation for Fig. A-E.

### Final figure outputs and meanings

`figA_rccn_ageing_reproduction.png`

- Meaning: RCCN recovery dynamics after nutrient restoration for different
  waiting times.
- x-axis: recovery time after nutrient restoration, in minutes.
- y-axis: mean cycle-averaged magnetization.
- Lines/colors: different `Tw` values; shaded bands show SEM.

`figB_umap_by_Tw_recovery_time.png`

- Meaning: UMAP state-space movement for selected `Tw` values and selected
  recovery snapshots.
- Panels: `Tw = 0, 488, 1346`.
- x-axis: UMAP1.
- y-axis: UMAP2.
- Colors: recovery snapshot time, currently `0`, `500`, and `2000` min.
- Marginal histograms: density of UMAP1 and UMAP2 for each recovery snapshot.
- Text annotation: experimental tail fraction matched for that `Tw`.

`figB_umap_recovery_time_exploration_6color.png`

- Meaning: exploratory version of Fig. B with finer recovery-time sampling.
- Panels: same selected `Tw` values.
- x-axis: UMAP1.
- y-axis: UMAP2.
- Colors: recovery snapshot time
  `0, 250, 500, 1000, 2000, 4000` min.

`figC_cluster_occupancy_lag_by_cluster.png`

- Meaning: relationship between spin-state clusters, waiting time, and recovery
  / lag time.
- Left panel x-axis: waiting time `Tw`, in minutes.
- Left panel y-axis: fraction of simulations.
- Left panel colors: KMeans spin-state cluster id.
- Right panel x-axis: spin-state cluster id.
- Right panel y-axis: recovery / lag time, in minutes.
- Right panel marks: violin distributions with individual simulated cells.

`figD_cycle_groups_along_PC1.png`

- Meaning: how cycle/loop groups contribute along the PC1 state axis.
- Top panel x-axis: PC1 score.
- Top panel y-axis: cell count.
- Bottom panel x-axis: PC1 window center.
- Bottom panel y-axis: mean cycle magnetization.
- Lines/colors: short, medium, and long cycle groups; shaded bands show SEM.
- Current interpretation target: whether medium-length loops dominate the
  activated/recovery-associated state direction.

`figE_presister_like_PCA_UMAP.png`

- Meaning: PCA and UMAP separation between normal and presister-like simulated
  cells using the tail-fraction-based label.
- Left panel x-axis: PC1.
- Left panel y-axis: PC2.
- Right panel x-axis: UMAP1.
- Right panel y-axis: UMAP2.
- Colors: `normal` versus `presister-like`.
- Marginal histograms: density of each labeled population along each embedding
  axis.

## Environment setup on a new computer

### Recommended system

For the full `result611` run, use a machine with more memory than the original
laptop if possible. A practical target is:

- Windows 10/11 or Linux/macOS with PowerShell available.
- 8 or more CPU cores.
- 32 GB RAM or more preferred for the full final run.
- Miniconda or Miniforge installed and available on `PATH`.

The simulation itself is CPU-based. No GPU/CUDA setup is required.

### Python dependencies

The project uses Python 3.11. The required packages are:

- `numpy`
- `pandas`
- `scipy`
- `matplotlib`
- `scikit-learn`
- `umap-learn`
- `openpyxl`
- `pytest`

These dependencies are recorded in:

```text
environment.yml
```

### Recommended stable analysis environment

For the final `result611` analysis and figure generation, the tested stable
environment is a conda-forge Python 3.11 environment using OpenBLAS and a
UMAP/scikit-learn version pair that works together on Windows:

```text
C:\work\env_rccn_stable
```

Create it with:

```powershell
conda create -p C:\work\env_rccn_stable -c conda-forge --strict-channel-priority python=3.11 "numpy=1.26.*" "scipy=1.11.*" "scikit-learn=1.4.*" pandas matplotlib umap-learn openpyxl pytest "libblas=*=*openblas" "liblapack=*=*openblas" -y
conda install -p C:\work\env_rccn_stable -c conda-forge "umap-learn=0.5.6" -y
```

Then verify:

```powershell
C:\work\env_rccn_stable\python.exe scripts\check_final_pipeline_imports.py
C:\work\env_rccn_stable\python.exe -m pytest tests
```

Before running final analysis with full PCA, set OpenBLAS/OMP threads:

```powershell
$env:OPENBLAS_NUM_THREADS="4"
$env:OMP_NUM_THREADS="4"
$env:NUMEXPR_NUM_THREADS="4"
```

Then run:

```powershell
C:\work\env_rccn_stable\python.exe scripts\run_final_state_analysis.py
C:\work\env_rccn_stable\python.exe scripts\make_final_project_figures.py
```

The final analysis uses full sklearn PCA by default. `IncrementalPCA` remains
available only as an explicit fallback through the internal `pca_method`
parameter.

Important Windows environment note:

- Avoid mixing pip-installed `scipy` with conda-forge `numpy` /
  `scikit-learn` / BLAS packages.
- In one failed environment, `python.exe` crashed during PCA with a native
  `APPCRASH` rather than a Python traceback.
- `umap-learn 0.5.12` was incompatible with `scikit-learn 1.4.2` in this run;
  `umap-learn 0.5.6` worked.

### Generic one-command setup and check

After installing Miniconda/Miniforge and cloning/copying this repository to the
new computer, open PowerShell in the project root and run:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\setup_result611_environment.ps1
```

This creates or updates a conda environment named:

```text
qbio_rccn_py311
```

Then it runs:

```powershell
scripts\check_final_pipeline_imports.py
```

to check that all required packages can be imported.

To create the environment at a specific path instead of by name:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\setup_result611_environment.ps1 -EnvPath C:\work\env
```

To also run the small unit-test suite after package installation:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\setup_result611_environment.ps1 -RunPytest
```

The setup script prints the `python.exe` path at the end. Use that path when
starting the full pipeline on a new computer, for example:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\run_result611_pipeline.ps1 -PythonExe "C:\work\env\python.exe" -Workers 4
```

If you use the default named conda environment, copy the `python.exe` path printed
by the setup script into `-PythonExe`.

### Manual conda installation commands

If you prefer to install manually, run:

```powershell
conda env create -f environment.yml
conda activate qbio_rccn_py311
python scripts\check_final_pipeline_imports.py
```

If the environment already exists:

```powershell
conda env update -n qbio_rccn_py311 -f environment.yml --prune
conda activate qbio_rccn_py311
python scripts\check_final_pipeline_imports.py
```

The full final pipeline can then be run with:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\run_result611_pipeline.ps1 -PythonExe "<path-to-qbio_rccn_py311-python.exe>" -Workers 4
```

For the known-good Windows analysis environment from 2026-06-11, prefer:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\run_result611_pipeline.ps1 -PythonExe "C:\work\env_rccn_stable\python.exe" -Workers 12
```

More detailed run notes, cleanup notes, and environment debugging records are in:

```text
cowithAI/0611running.md
```

# Set 4 Question 2 — Step 1 Codex Guidance

## 0. Purpose of this document

This document is a scientific coding instruction for Codex.

The goal is **not** to build a complete predator–prey modeling framework yet.  
The goal is to perform the **first exploratory step** for Problem Set 4, Question 2:

> Use the raw data from `eco_data.xlsx` to visualize the two rotifer–alga co-culture experiments and compare their qualitative predator–prey dynamics.

This first step should generate a small number of clear figures and a concise summary table that help us decide whether simple predator–prey models discussed in class are appropriate.

Do **not** over-engineer the code.  
Do **not** fit complicated models yet.  
Do **not** build a general reusable package.  
This should be a short, transparent scientific analysis script or notebook.

---

## 1. Scientific background

Problem Set 4 Question 2 asks whether species abundance data from two rotifer–alga co-culture experiments can be modeled using predator–prey models discussed in class.

The biological system is:

- **Prey**: alga species
- **Predator**: rotifer species
- **Data**: abundance time series from two experiments
- **Source**: Yoshida et al. Nature (2003), as indicated in the problem set

The key scientific question is:

> Do the two experiments show predator–prey oscillations, and are these oscillations consistent with the qualitative predictions of simple predator–prey models?

A secondary question is:

> Are there notable differences between the two experiments, such as differences in oscillation period, amplitude, phase lag, or stability?

At this stage, we only want to visualize and describe the raw dynamics.

---

## 2. Scientific model to keep in mind

The simplest predator–prey model is the Lotka–Volterra model:

```math
\frac{dN}{dt} = rN - aNP
```

```math
\frac{dP}{dt} = baNP - dP
```

where:

- `N(t)` = prey abundance, here alga abundance
- `P(t)` = predator abundance, here rotifer abundance
- `r` = prey intrinsic growth rate
- `a` = predation rate
- `b` = conversion efficiency from consumed prey to predator growth
- `d` = predator death rate

The qualitative feedback loop is:

```text
alga increases
    → rotifer has more food and increases later
        → rotifer suppresses alga
            → alga decline causes rotifer decline
                → alga can recover again
```

Therefore, in the raw data, the most important qualitative feature to inspect is:

> Does the predator peak lag behind the prey peak?

If yes, the simple predator–prey picture is qualitatively useful.

However, real experimental data may require more realistic models later, for example:

```math
\frac{dN}{dt} = rN\left(1 - \frac{N}{K}\right) - aNP
```

```math
\frac{dP}{dt} = baNP - dP
```

This includes prey carrying capacity `K`.  
But **do not fit this model in Step 1**.  
Only keep it in mind when interpreting whether the raw data look like predator–prey dynamics.

---

## 3. Step 1 goal

Write a simple Python script or notebook that:

1. Reads `eco_data.xlsx`.
2. Identifies the two experiments in the file.
3. Identifies time, alga abundance, and rotifer abundance columns.
4. Plots raw and normalized abundance time series for each experiment.
5. Optionally plots a phase portrait: rotifer abundance versus alga abundance.
6. Produces a small summary table for comparing the two experiments.
7. Saves the figures and summary table to an output folder.

This step should answer:

- Do both experiments show oscillations?
- Does rotifer abundance lag behind alga abundance?
- Are the two experiments similar or different in period, amplitude, and phase relationship?
- Is the simple predator–prey model a reasonable qualitative starting point?

---

## 4. Inputs

The expected input file is:

```text
eco_data.xlsx
```

The exact sheet names and column names are unknown before inspection.

Codex should first generate a small inspection step that prints:

- sheet names
- column names of each sheet
- first few rows of each sheet

Do not write complex automatic column inference unless necessary.  
Prefer explicit, readable handling after inspecting the file.

If column names are clear, use them directly.

---

## 5. Outputs

Create an output folder, for example:

```text
outputs/set4_q2_step1/
```

Save these outputs:

### Main figures

1. `experiment_1_raw_timeseries.png`
   - x-axis: time
   - y-axis: abundance
   - plot alga and rotifer together

2. `experiment_2_raw_timeseries.png`
   - same as above

3. `experiments_normalized_comparison.png`
   - normalized abundance time series
   - useful if alga and rotifer have very different numerical scales
   - each abundance can be divided by its own maximum within each experiment

4. `phase_portraits.png`
   - x-axis: alga abundance
   - y-axis: rotifer abundance
   - one panel or one figure per experiment
   - useful for seeing cyclic predator–prey dynamics

### Summary table

Save:

```text
experiment_summary.csv
```

Suggested columns:

- `experiment`
- `n_timepoints`
- `time_min`
- `time_max`
- `alga_min`
- `alga_max`
- `rotifer_min`
- `rotifer_max`
- `time_of_alga_max`
- `time_of_rotifer_max`
- `rotifer_peak_minus_alga_peak`

The last column is a simple estimate of phase lag.  
If `rotifer_peak_minus_alga_peak > 0`, the predator peak occurs after the prey peak, which supports the predator–prey interpretation.

Do not over-interpret this value if the time series has multiple peaks.  
It is only a first-pass summary.

---

## 6. Recommended minimal workflow

Use a simple notebook or one Python script with the following structure.

```text
Cell / Section 1: imports and paths
Cell / Section 2: inspect Excel file
Cell / Section 3: load and clean the two experiments
Cell / Section 4: plot raw time series
Cell / Section 5: plot normalized comparison
Cell / Section 6: plot phase portraits
Cell / Section 7: compute and save summary table
Cell / Section 8: write a short printed interpretation
```

Avoid unnecessary classes.  
Avoid complex configuration systems.  
Avoid broad try/except blocks.

---

## 7. Function-level pseudocode

### 7.1 `inspect_excel_file(excel_path)`

#### Purpose

Inspect the structure of `eco_data.xlsx` before deciding how to parse it.

#### Input

- `excel_path`: path to the Excel file

#### Output

- prints sheet names
- prints column names and first few rows of each sheet

#### Pseudocode

```text
function inspect_excel_file(excel_path):
    1. Open the Excel file using pandas.ExcelFile
    2. Print all sheet names
    3. For each sheet:
        a. Read the sheet into a dataframe
        b. Print sheet name
        c. Print dataframe shape
        d. Print column names
        e. Print first few rows
```

#### Code type

Auxiliary inspection logic.

---

### 7.2 `load_experiment_tables(excel_path)`

#### Purpose

Load the two experiment tables after the file structure is known.

#### Input

- `excel_path`: path to `eco_data.xlsx`

#### Output

- `experiments`: a dictionary such as:

```python
{
    "experiment_1": df1,
    "experiment_2": df2,
}
```

Each dataframe should contain at least:

- `time`
- `alga`
- `rotifer`

#### Pseudocode

```text
function load_experiment_tables(excel_path):
    1. Read the relevant sheet or sheets from the Excel file
    2. Rename columns into simple standard names:
        - time
        - alga
        - rotifer
    3. Keep only these columns
    4. Sort each experiment by time
    5. Return a dictionary containing the two cleaned dataframes
```

#### Code type

Main data loading logic.

#### Important note

Because the exact Excel structure is unknown, Codex should write this function in a way that is easy to modify after inspection.  
Do not write complicated automatic guessing unless the column names are messy.

---

### 7.3 `normalize_abundance(df)`

#### Purpose

Create normalized alga and rotifer columns so that the two species can be plotted on comparable scales.

#### Input

- `df`: dataframe with `time`, `alga`, `rotifer`

#### Output

- dataframe with additional columns:
  - `alga_norm`
  - `rotifer_norm`

#### Formula

```math
N_{norm}(t) = \frac{N(t)}{\max_t N(t)}
```

```math
P_{norm}(t) = \frac{P(t)}{\max_t P(t)}
```

#### Pseudocode

```text
function normalize_abundance(df):
    1. Copy the dataframe
    2. Divide alga abundance by maximum alga abundance
    3. Divide rotifer abundance by maximum rotifer abundance
    4. Return the copied dataframe
```

#### Code type

Small helper logic.

---

### 7.4 `plot_raw_timeseries(experiments, output_dir)`

#### Purpose

Plot raw alga and rotifer abundances over time for each experiment.

#### Input

- `experiments`: dictionary of cleaned experiment dataframes
- `output_dir`: folder for saving figures

#### Output

- one raw time series figure per experiment

#### Pseudocode

```text
function plot_raw_timeseries(experiments, output_dir):
    1. For each experiment:
        a. Create a figure
        b. Plot alga abundance versus time
        c. Plot rotifer abundance versus time
        d. Label axes clearly
        e. Add legend
        f. Save figure
```

#### Code type

Main plotting logic.

---

### 7.5 `plot_normalized_comparison(experiments, output_dir)`

#### Purpose

Plot normalized alga and rotifer time series so that phase relationships can be compared visually.

#### Input

- `experiments`: dictionary of cleaned experiment dataframes
- `output_dir`: folder for saving figures

#### Output

- one figure comparing normalized dynamics across experiments

#### Pseudocode

```text
function plot_normalized_comparison(experiments, output_dir):
    1. For each experiment:
        a. Normalize alga and rotifer abundance
        b. Plot normalized alga versus time
        c. Plot normalized rotifer versus time
    2. Use clear labels to distinguish experiment and species
    3. Save figure
```

#### Code type

Main plotting logic.

---

### 7.6 `plot_phase_portraits(experiments, output_dir)`

#### Purpose

Plot rotifer abundance against alga abundance for each experiment.

This helps visualize whether the system follows a cyclic predator–prey trajectory.

#### Input

- `experiments`: dictionary of cleaned experiment dataframes
- `output_dir`: folder for saving figures

#### Output

- one phase portrait figure

#### Pseudocode

```text
function plot_phase_portraits(experiments, output_dir):
    1. For each experiment:
        a. Plot rotifer abundance on y-axis
        b. Plot alga abundance on x-axis
        c. Connect points in time order
        d. Optionally annotate start and end points
    2. Save figure
```

#### Code type

Auxiliary plotting logic.

---

### 7.7 `summarize_experiment(df, experiment_name)`

#### Purpose

Compute a minimal numerical summary for one experiment.

#### Input

- `df`: cleaned dataframe with `time`, `alga`, `rotifer`
- `experiment_name`: name of experiment

#### Output

- one-row dictionary or dataframe

#### Pseudocode

```text
function summarize_experiment(df, experiment_name):
    1. Count number of time points
    2. Find minimum and maximum time
    3. Find min and max alga abundance
    4. Find min and max rotifer abundance
    5. Find time where alga reaches its maximum
    6. Find time where rotifer reaches its maximum
    7. Compute rotifer_peak_minus_alga_peak
    8. Return one summary row
```

#### Code type

Main scientific summary logic.

---

### 7.8 `summarize_all_experiments(experiments, output_dir)`

#### Purpose

Create and save the summary table for both experiments.

#### Input

- `experiments`: dictionary of cleaned experiment dataframes
- `output_dir`: folder for saving results

#### Output

- `experiment_summary.csv`
- summary dataframe

#### Pseudocode

```text
function summarize_all_experiments(experiments, output_dir):
    1. Run summarize_experiment for each experiment
    2. Combine rows into a dataframe
    3. Save dataframe as experiment_summary.csv
    4. Return dataframe
```

#### Code type

Main scientific summary logic and saving output.

---

### 7.9 `print_short_interpretation(summary)`

#### Purpose

Print a short first-pass interpretation based on peak timing.

#### Input

- `summary`: summary dataframe

#### Output

- printed text

#### Pseudocode

```text
function print_short_interpretation(summary):
    1. For each experiment:
        a. Read rotifer_peak_minus_alga_peak
        b. If positive, print that predator peak occurs after prey peak
        c. If near zero, print that peaks occur at similar times
        d. If negative, print that predator peak occurs before prey peak
    2. Print reminder:
        This is only a first-pass summary and should be interpreted together with the figures.
```

#### Code type

Auxiliary interpretation logic.

---

### 7.10 `run_step1_pipeline(excel_path, output_dir)`

#### Purpose

Run the full Step 1 exploratory analysis.

#### Input

- `excel_path`: path to `eco_data.xlsx`
- `output_dir`: output folder

#### Output

- saved figures
- saved summary table
- printed interpretation

#### Pseudocode

```text
function run_step1_pipeline(excel_path, output_dir):
    1. Create output directory
    2. Inspect Excel file structure
    3. Load cleaned experiment tables
    4. Plot raw time series
    5. Plot normalized comparison
    6. Plot phase portraits
    7. Compute and save summary table
    8. Print short interpretation
```

#### Code type

Main pipeline.

---

## 8. What not to do in Step 1

Do not implement these yet:

1. Full ODE parameter fitting
2. Bayesian inference
3. Bootstrapping confidence intervals
4. Model selection using AIC
5. Eco-evolutionary model fitting
6. Automatic detection of all oscillation peaks
7. Complex smoothing
8. Complex missing-value imputation
9. General-purpose Excel parser
10. A large package-like code structure

These may be considered in later steps after we inspect the raw dynamics.

---

## 9. Expected scientific interpretation after Step 1

After the code runs, the figures and summary table should help us write a statement like:

```text
Both experiments show coupled alga–rotifer dynamics, but they differ in the timing, amplitude, or regularity of oscillations. In experiment X, the rotifer peak appears after the alga peak, which is qualitatively consistent with a predator–prey feedback loop. In experiment Y, the phase relationship is different / weaker / more delayed, suggesting that a simple Lotka–Volterra model may be insufficient. These differences motivate considering more realistic ecological or eco-evolutionary models in the next step.
```

Do not force this conclusion before seeing the figures.  
The code should reveal the pattern first.

---

## 10. Minimal coding style

Use:

```python
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
```

Possibly use:

```python
import openpyxl
```

Do not use heavy dependencies unless needed.

The code should be easy to paste into a notebook or save as:

```text
set4_q2_step1_explore_eco_data.py
```

Prefer clear functions and simple plotting over abstraction.

---

## 11. Deliverable requested from Codex

Please generate either:

1. A short Python script named `set4_q2_step1_explore_eco_data.py`, or
2. A notebook-style sequence of code cells

The deliverable should:

- inspect the Excel file
- load two experiments
- standardize columns to `time`, `alga`, `rotifer`
- make raw time series plots
- make normalized comparison plot
- make phase portrait plot
- save `experiment_summary.csv`
- print a short first-pass interpretation

Keep the implementation short, readable, and easy to modify after inspecting the actual Excel structure.

param(
    [string]$PythonExe = "F:\conda_envs\e_coli_rpy2_py311\python.exe",
    [switch]$WithChecks,
    [int]$Workers = 4
)

$ErrorActionPreference = "Stop"

$Runner = Join-Path $PSScriptRoot "run_overnight_final_pipeline.ps1"
$Arguments = @(
    "-NoProfile",
    "-ExecutionPolicy",
    "Bypass",
    "-File",
    $Runner,
    "-PythonExe",
    $PythonExe,
    "-Workers",
    "$Workers"
)

if (-not $WithChecks) {
    $Arguments += "-DirectFullRun"
}

& powershell @Arguments
exit $LASTEXITCODE

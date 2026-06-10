param(
    [string]$PythonExe = "F:\conda_envs\e_coli_rpy2_py311\python.exe",
    [string]$RunName = "",
    [switch]$DirectFullRun,
    [switch]$SkipDependencyCheck,
    [switch]$SkipPytest,
    [switch]$SkipSmoke,
    [switch]$SmokeOnly
)

$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $ProjectRoot

if (-not (Test-Path -LiteralPath $PythonExe)) {
    throw "Python executable not found: $PythonExe"
}

$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
if ([string]::IsNullOrWhiteSpace($RunName)) {
    $RunName = "final_pipeline_$Timestamp"
}

$RunDir = Join-Path $ProjectRoot "output\overnight_runs\$RunName"
$LogDir = Join-Path $RunDir "logs"
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

function Write-RunLog {
    param([string]$Message)
    $Line = "{0}  {1}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $Message
    $Line | Tee-Object -FilePath (Join-Path $RunDir "run.log") -Append
}

function Invoke-LoggedStep {
    param(
        [string]$Name,
        [string[]]$Arguments
    )

    $Stdout = Join-Path $LogDir "$Name.stdout.log"
    $Stderr = Join-Path $LogDir "$Name.stderr.log"
    $ArgText = ($Arguments -join " ")
    Write-RunLog "START $Name`: $PythonExe $ArgText"

    $Process = Start-Process `
        -FilePath $PythonExe `
        -ArgumentList $Arguments `
        -WorkingDirectory $ProjectRoot `
        -NoNewWindow `
        -Wait `
        -PassThru `
        -RedirectStandardOutput $Stdout `
        -RedirectStandardError $Stderr

    Write-RunLog "END   $Name`: exit_code=$($Process.ExitCode)"
    if ($Process.ExitCode -ne 0) {
        throw "Step failed: $Name. See $Stdout and $Stderr"
    }
}

function Move-OutputIfPresent {
    param(
        [string]$RelativePath,
        [string]$DestinationName
    )

    $Source = Join-Path $ProjectRoot $RelativePath
    if (Test-Path -LiteralPath $Source) {
        $Destination = Join-Path $RunDir $DestinationName
        New-Item -ItemType Directory -Force -Path (Split-Path -Parent $Destination) | Out-Null
        if (Test-Path -LiteralPath $Destination) {
            throw "Refusing to overwrite existing archive path: $Destination"
        }
        Move-Item -LiteralPath $Source -Destination $Destination
        Write-RunLog "MOVED $RelativePath -> $Destination"
    }
}

Write-RunLog "Run directory: $RunDir"
Write-RunLog "Python: $PythonExe"
& $PythonExe --version 2>&1 | Tee-Object -FilePath (Join-Path $RunDir "python_version.log")

if ($DirectFullRun) {
    $SkipDependencyCheck = $true
    $SkipPytest = $true
    $SkipSmoke = $true
}

if (-not $SkipDependencyCheck) {
    Invoke-LoggedStep "check_imports" @(
        "scripts\check_final_pipeline_imports.py"
    )
}

if (-not $SkipPytest) {
    Invoke-LoggedStep "pytest" @("-m", "pytest", "tests")
}

if (-not $SkipSmoke) {
    try {
        Invoke-LoggedStep "smoke_final_simulation" @(
            "scripts\run_final_rccn_simulation.py",
            "--preset",
            "smoke"
        )
        Invoke-LoggedStep "smoke_final_analysis" @("scripts\run_final_state_analysis.py")
        Invoke-LoggedStep "smoke_final_figures" @("scripts\make_final_project_figures.py")
    }
    finally {
        Move-OutputIfPresent "output\final_simulation" "smoke_outputs\final_simulation"
        Move-OutputIfPresent "output\final_analysis" "smoke_outputs\final_analysis"
        Move-OutputIfPresent "output\final_figures" "smoke_outputs\final_figures"
    }
}

if ($SmokeOnly) {
    Write-RunLog "DONE smoke-only test. Full final pipeline was not started."
    exit 0
}

Invoke-LoggedStep "full_final_simulation" @(
    "scripts\run_final_rccn_simulation.py",
    "--preset",
    "final"
)
Invoke-LoggedStep "full_final_analysis" @("scripts\run_final_state_analysis.py")
Invoke-LoggedStep "full_final_figures" @("scripts\make_final_project_figures.py")

Write-RunLog "DONE final outputs are in output\final_simulation, output\final_analysis, output\final_figures"

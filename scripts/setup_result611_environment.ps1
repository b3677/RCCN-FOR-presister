param(
    [string]$EnvName = "qbio_rccn_py311",
    [string]$EnvPath = "",
    [switch]$RunPytest
)

$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$EnvironmentFile = Join-Path $ProjectRoot "environment.yml"
$CheckScript = Join-Path $ProjectRoot "scripts\check_final_pipeline_imports.py"

if (-not (Test-Path -LiteralPath $EnvironmentFile)) {
    throw "environment.yml not found: $EnvironmentFile"
}

$CondaCommand = Get-Command conda -ErrorAction SilentlyContinue
if ($null -eq $CondaCommand) {
    throw "conda was not found on PATH. Install Miniconda/Miniforge first, then rerun this script."
}

Set-Location $ProjectRoot

function Invoke-Step {
    param(
        [string]$Message,
        [string[]]$Command
    )

    Write-Host ""
    Write-Host "[setup] $Message"
    Write-Host "[setup] $($Command -join ' ')"
    $Exe = $Command[0]
    $Args = @()
    if ($Command.Length -gt 1) {
        $Args = $Command[1..($Command.Length - 1)]
    }
    & $Exe @Args
    if ($LASTEXITCODE -ne 0) {
        throw "Command failed: $($Command -join ' ')"
    }
}

if ([string]::IsNullOrWhiteSpace($EnvPath)) {
    $envExists = $false
    $envList = conda env list
    foreach ($line in $envList) {
        if ($line -match "^\s*$([regex]::Escape($EnvName))\s+") {
            $envExists = $true
            break
        }
    }

    if ($envExists) {
        Invoke-Step "Updating existing conda env: $EnvName" @(
            "conda", "env", "update", "-n", $EnvName, "-f", $EnvironmentFile, "--prune"
        )
    }
    else {
        Invoke-Step "Creating conda env: $EnvName" @(
            "conda", "env", "create", "-n", $EnvName, "-f", $EnvironmentFile
        )
    }

    Invoke-Step "Checking required Python packages" @(
        "conda", "run", "-n", $EnvName, "python", $CheckScript
    )

    if ($RunPytest) {
        Invoke-Step "Running project tests" @(
            "conda", "run", "-n", $EnvName, "python", "-m", "pytest", "tests"
        )
    }

    $PythonExe = (& conda run -n $EnvName python -c "import sys; print(sys.executable)")[-1]

    Write-Host ""
    Write-Host "[setup] Done."
    Write-Host "[setup] Use this Python for the final pipeline:"
    Write-Host "[setup] $PythonExe"
    Write-Host "[setup] Full pipeline command:"
    Write-Host "[setup] powershell -ExecutionPolicy Bypass -File scripts\run_result611_pipeline.ps1 -PythonExe `"$PythonExe`""
}
else {
    $EnvPath = (Resolve-Path -Path $EnvPath -ErrorAction SilentlyContinue).Path
    if ([string]::IsNullOrWhiteSpace($EnvPath)) {
        $EnvPath = $PSBoundParameters["EnvPath"]
    }
    $EnvironmentFileForPath = Join-Path ([System.IO.Path]::GetTempPath()) "qbio_rccn_environment_no_name.yml"
    Get-Content -Path $EnvironmentFile |
        Where-Object { $_ -notmatch "^\s*name\s*:" } |
        Set-Content -Path $EnvironmentFileForPath

    if (Test-Path -LiteralPath $EnvPath) {
        Invoke-Step "Updating existing conda env at: $EnvPath" @(
            "conda", "env", "update", "-p", $EnvPath, "-f", $EnvironmentFileForPath, "--prune"
        )
    }
    else {
        Invoke-Step "Creating conda env at: $EnvPath" @(
            "conda", "env", "create", "-p", $EnvPath, "-f", $EnvironmentFileForPath
        )
    }

    Invoke-Step "Checking required Python packages" @(
        "conda", "run", "-p", $EnvPath, "python", $CheckScript
    )

    if ($RunPytest) {
        Invoke-Step "Running project tests" @(
            "conda", "run", "-p", $EnvPath, "python", "-m", "pytest", "tests"
        )
    }

    $PythonExe = Join-Path $EnvPath "python.exe"

    Write-Host ""
    Write-Host "[setup] Done."
    Write-Host "[setup] Use this Python for the final pipeline:"
    Write-Host "[setup] $EnvPath\python.exe"
    Write-Host "[setup] Full pipeline command:"
    Write-Host "[setup] powershell -ExecutionPolicy Bypass -File scripts\run_result611_pipeline.ps1 -PythonExe `"$PythonExe`""
}

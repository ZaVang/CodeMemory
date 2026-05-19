[CmdletBinding()]
param(
    [int]$BackendPort = 0,
    [int]$FrontendPort = 0,
    [string]$HostName = "",
    [switch]$SkipInstall
)

$ErrorActionPreference = "Stop"

$Root = $PSScriptRoot
$FrontendDir = Join-Path $Root "frontend"
$Launcher = Join-Path $Root "bin\codememory.py"

if ($BackendPort -le 0) {
    $BackendPort = if ($env:BACKEND_PORT) { [int]$env:BACKEND_PORT } else { 8000 }
}

if ($FrontendPort -le 0) {
    $FrontendPort = if ($env:FRONTEND_PORT) { [int]$env:FRONTEND_PORT } else { 5300 }
}

if ([string]::IsNullOrWhiteSpace($HostName)) {
    $HostName = if ($env:DEV_HOST) { $env:DEV_HOST } else { "127.0.0.1" }
}

function Get-RequiredCommand {
    param(
        [string[]]$Names,
        [string]$InstallHint
    )

    foreach ($Name in $Names) {
        $Command = Get-Command $Name -ErrorAction SilentlyContinue
        if ($Command) {
            return $Command
        }
    }

    throw "Missing required command: $($Names -join ' or '). $InstallHint"
}

if (-not (Test-Path -LiteralPath $Launcher)) {
    throw "Missing launcher: $Launcher"
}

if (-not (Test-Path -LiteralPath (Join-Path $FrontendDir "package.json"))) {
    throw "Missing frontend package.json: $FrontendDir"
}

$Python = Get-RequiredCommand -Names @("python", "py") -InstallHint "Install Python 3.13+ and make it available on PATH."
$Npm = Get-RequiredCommand -Names @("npm.cmd", "npm") -InstallHint "Install Node.js/npm and make it available on PATH."

$NodeModules = Join-Path $FrontendDir "node_modules"
if (-not $SkipInstall -and -not (Test-Path -LiteralPath $NodeModules)) {
    Write-Host "[setup] frontend\node_modules not found; running npm install..."
    Push-Location $FrontendDir
    try {
        & $Npm.Source install
    }
    finally {
        Pop-Location
    }
}

Write-Host ""
Write-Host "Starting CodeMemory..."
Write-Host "Frontend: http://$HostName`:$FrontendPort"
Write-Host "Backend:  http://$HostName`:$BackendPort"
Write-Host ""

$PythonArgs = @()
if ($Python.Name -eq "py" -or $Python.Name -eq "py.exe") {
    $PythonArgs += "-3"
}

$PythonArgs += @(
    $Launcher,
    "dev",
    "--backend-port", "$BackendPort",
    "--frontend-port", "$FrontendPort",
    "--host", "$HostName"
)

& $Python.Source @PythonArgs
exit $LASTEXITCODE

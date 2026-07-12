[CmdletBinding()]
param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$SetupArgs
)

$ErrorActionPreference = "Stop"
$Wsl = Get-Command wsl.exe -ErrorAction SilentlyContinue
if (-not $Wsl) {
    throw "WSL is required for Plane's upstream setup script. Enable WSL, install a Linux distribution, and enable Docker Desktop WSL integration."
}

Write-Host "Running the Plane setup through WSL from $PSScriptRoot"
& $Wsl.Source --cd $PSScriptRoot bash ./setup.sh @SetupArgs
exit $LASTEXITCODE

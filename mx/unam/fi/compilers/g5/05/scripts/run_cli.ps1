$ErrorActionPreference = "Stop"
$RootDir = Split-Path -Parent $PSScriptRoot
Set-Location (Join-Path $RootDir "src")
python main.py @args

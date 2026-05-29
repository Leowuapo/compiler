# PENTA Compiler - documentación interna
# Script de PowerShell para ejecutar la GUI o CLI desde la carpeta correcta.
# Mantiene la llamada simple para usuarios de Windows.

$ErrorActionPreference = "Stop"
$RootDir = Split-Path -Parent $PSScriptRoot
Set-Location (Join-Path $RootDir "src")
python main.py @args

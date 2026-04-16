#!/usr/bin/env pwsh
$scriptPath = Join-Path $PSScriptRoot "..\..\src\dahua-cloud-ai-cli.py"
python $scriptPath @args

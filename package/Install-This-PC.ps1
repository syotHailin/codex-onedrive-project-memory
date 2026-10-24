[CmdletBinding()]
param([string]$DeviceName=$env:COMPUTERNAME)
$ErrorActionPreference='Stop'
$sharedRoot=Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$marker=Join-Path $sharedRoot 'CodexSharedMemory.Library.json'
if(-not (Test-Path -LiteralPath $marker)) { throw 'Run this launcher from the synchronized Codex-Shared-Memory\setup\v1.0.0 folder, or use Install.ps1 -SharedRoot with an explicit path.' }
$library=Get-Content -LiteralPath $marker -Raw -Encoding UTF8|ConvertFrom-Json
if($library.library_type -ne 'codex-project-memory' -or $library.schema_version -ne 1){throw 'Unrecognized shared library.'}
& (Join-Path $PSScriptRoot 'Install.ps1') -SharedRoot $sharedRoot -DeviceName $DeviceName

[CmdletBinding()]
param([Parameter(Mandatory=$true)][string]$ProjectPath,[Parameter(Mandatory=$true)][string]$ProjectId)
$ErrorActionPreference='Stop'
$taskCodexRoot=if($env:CODEX_HOME){$env:CODEX_HOME}else{Join-Path $env:USERPROFILE '.codex'}
$runtime=Join-Path $taskCodexRoot 'skills\onedrive-project-memory\scripts\memory.ps1'
& $runtime -Action Bind -ProjectPath $ProjectPath -ProjectId $ProjectId

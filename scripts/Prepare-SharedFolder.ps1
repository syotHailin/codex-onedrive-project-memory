[CmdletBinding()]
param([Parameter(Mandatory=$true)][string]$SharedRoot)
$ErrorActionPreference='Stop'
$utf8=New-Object System.Text.UTF8Encoding($false)
function File-Hash([string]$Path) {
    $sha=[Security.Cryptography.SHA256]::Create()
    $stream=[IO.File]::OpenRead($Path)
    try { return [BitConverter]::ToString($sha.ComputeHash($stream)) } finally { $stream.Dispose(); $sha.Dispose() }
}
$shared=[IO.Path]::GetFullPath($SharedRoot).TrimEnd([char[]]'\/')
if(-not (Test-Path -LiteralPath (Split-Path -Parent $shared) -PathType Container)) { throw 'The parent folder must exist. Choose the actual local OneDrive folder.' }
$source=Join-Path (Split-Path -Parent $PSScriptRoot) 'package'
$setup=Join-Path $shared 'setup\v1.0.0'
$marker=Join-Path $shared 'CodexSharedMemory.Library.json'
if(-not (Test-Path -LiteralPath (Join-Path $source 'Install.ps1'))) { throw 'Keep scripts beside the package folder from this repository.' }
if(Test-Path -LiteralPath $marker) {
    $existing=[IO.File]::ReadAllText($marker,$utf8)|ConvertFrom-Json
    if($existing.library_type -ne 'codex-project-memory' -or $existing.schema_version -ne 1) { throw 'Unrecognized shared library marker.' }
}
$files=@(Get-ChildItem -LiteralPath $source -File -Recurse)
foreach($file in $files) {
    $relative=$file.FullName.Substring($source.Length).TrimStart([char[]]'\/')
    $destination=Join-Path $setup $relative
    if((Test-Path -LiteralPath $destination) -and (File-Hash $file.FullName) -ne (File-Hash $destination)) { throw "Existing setup differs; no files replaced. Review version before publishing: $relative" }
}
[void][IO.Directory]::CreateDirectory($setup)
if(-not (Test-Path -LiteralPath $marker)) {
    $value=@{library_type='codex-project-memory';schema_version=1;library_id=[guid]::NewGuid().ToString();created_utc=[DateTime]::UtcNow.ToString('o')}
    $stream=[IO.File]::Open($marker,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::None)
    try { $bytes=$utf8.GetBytes(($value|ConvertTo-Json)); $stream.Write($bytes,0,$bytes.Length) } finally { $stream.Dispose() }
}
foreach($file in $files) {
    $relative=$file.FullName.Substring($source.Length).TrimStart([char[]]'\/')
    $destination=Join-Path $setup $relative
    [void][IO.Directory]::CreateDirectory((Split-Path -Parent $destination))
    if(-not [IO.File]::Exists($destination)) { [IO.File]::Copy($file.FullName,$destination,$false) }
    if((File-Hash $file.FullName) -ne (File-Hash $destination)) { throw "Verification failed: $relative" }
}
[pscustomobject]@{prepared=$true;version='1.0.0';shared_setup=$setup;verified_files=$files.Count;next_step='Run Install-This-PC.cmd in the shared setup folder on each computer, then review /hooks.'}|ConvertTo-Json

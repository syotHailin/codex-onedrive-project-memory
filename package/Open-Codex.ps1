$ErrorActionPreference='Stop'
$exe=$null
$available=Get-Command codex -ErrorAction SilentlyContinue | Select-Object -First 1
if($available){$exe=$available.Source}
if(-not $exe){
    $bundled=Join-Path $env:LOCALAPPDATA 'OpenAI\Codex\bin'
    if(Test-Path -LiteralPath $bundled){
        $candidate=Get-ChildItem -LiteralPath $bundled -Filter 'codex.exe' -File -Recurse | Sort-Object LastWriteTime -Descending | Select-Object -First 1
        if($candidate){$exe=$candidate.FullName}
    }
}
if(-not $exe){throw 'Codex CLI was not found. Install or update the Codex desktop app, then retry.'}
Write-Host 'After Codex opens, type /hooks and trust the three onedrive-project-memory hooks.'
& $exe --no-daemon

[CmdletBinding()]
param([string]$CodexRoot)
$ErrorActionPreference='Stop'
if (-not $CodexRoot) { $CodexRoot=if($env:CODEX_HOME){$env:CODEX_HOME}else{Join-Path $env:USERPROFILE '.codex'} }
$utf8=New-Object System.Text.UTF8Encoding($false)
$local=Join-Path $CodexRoot 'shared-memory'
$backup=Join-Path $local ('backups\disable-' + [guid]::NewGuid().ToString('N'))
[void][IO.Directory]::CreateDirectory($backup)
$hookFile=Join-Path $CodexRoot 'hooks.json'
if(Test-Path -LiteralPath $hookFile){
    Copy-Item -LiteralPath $hookFile -Destination (Join-Path $backup 'hooks.json')
    $hooks=[IO.File]::ReadAllText($hookFile,$utf8)|ConvertFrom-Json
    foreach($event in @('SessionStart','UserPromptSubmit','Stop')){
        if($hooks.hooks.PSObject.Properties[$event]){
            $groups=@()
            foreach($group in @($hooks.hooks.$event)){
                $keep=@($group.hooks|Where-Object{$_.command -notmatch 'onedrive-project-memory[\\/]scripts[\\/]memory\.ps1'})
                if($keep.Count -gt 0){$group.hooks=$keep;$groups+=$group}
            }
            $hooks.hooks.$event=$groups
        }
    }
    [IO.File]::WriteAllText($hookFile,($hooks|ConvertTo-Json -Depth 30),$utf8)
}
foreach($name in @('AGENTS.md','AGENTS.override.md')){
    $path=Join-Path $CodexRoot $name
    if(Test-Path -LiteralPath $path){
        $old=[IO.File]::ReadAllText($path,$utf8)
        if($old.Contains('<!-- BEGIN ONEDRIVE-PROJECT-MEMORY -->')){
            Copy-Item -LiteralPath $path -Destination (Join-Path $backup $name)
            $new=[regex]::Replace($old,'(?s)<!-- BEGIN ONEDRIVE-PROJECT-MEMORY -->.*?<!-- END ONEDRIVE-PROJECT-MEMORY -->','')
            [IO.File]::WriteAllText($path,$new,$utf8)
        }
    }
}
$configFile=Join-Path $local 'config.json'
if(Test-Path -LiteralPath $configFile){
    $config=[IO.File]::ReadAllText($configFile,$utf8)|ConvertFrom-Json
    $config.enabled=$false
    [IO.File]::WriteAllText($configFile,($config|ConvertTo-Json -Depth 10),$utf8)
}
Write-Output 'Automatic hooks and guidance disabled. Restart Codex. Shared notes, skill files, local outbox and backups have been preserved.'

#requires -Version 5.1
$ErrorActionPreference = 'Stop'

$src = Join-Path $PSScriptRoot 'mods\ru_RU'
if (-not (Test-Path (Join-Path $src 'index.js'))) {
    throw "Не найден $src\index.js. Соберите мод: python tools\build_mod.py"
}

$modsDir = Join-Path $env:APPDATA 'spacetime\mods'
$dest = Join-Path $modsDir 'ru_RU'
New-Item -ItemType Directory -Force -Path $modsDir | Out-Null

if (Test-Path $dest) {
    $backup = "$dest.backup.$(Get-Date -Format 'yyyyMMdd-HHmmss')"
    Move-Item $dest $backup
    Write-Host "Предыдущая версия мода сохранена: $backup"
}

Copy-Item -Recurse -Force $src $dest
Write-Host "Мод установлен: $dest"
Write-Host "Запустите Outertale. При первом запуске русский язык включится автоматически."
Write-Host "Сменить язык можно в настройках: ЯЗЫК (LANGUAGE)."

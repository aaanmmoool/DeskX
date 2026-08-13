<#
.SYNOPSIS
    Build the distributable Windows package for DeskX.

.DESCRIPTION
    Regenerates the app icon, runs PyInstaller against packaging/DeskX.spec,
    drops the end-user readme into the bundle, and zips the result to
    release/DeskX-Windows.zip.

    Run from anywhere; paths are resolved relative to the repo root.

.EXAMPLE
    .\packaging\build_windows.ps1
#>

$ErrorActionPreference = "Stop"

$Root    = Split-Path -Parent $PSScriptRoot
$Venv    = Join-Path $Root ".venv\Scripts\python.exe"
$Dist    = Join-Path $Root "dist"
$Build   = Join-Path $Root "build"
$Release = Join-Path $Root "release"
$Zip     = Join-Path $Release "DeskX-Windows.zip"

$Python = if (Test-Path $Venv) { $Venv } else { "python" }

Write-Host "==> Using $Python" -ForegroundColor Cyan

Write-Host "==> Generating application icon" -ForegroundColor Cyan
& $Python (Join-Path $Root "packaging\make_icon.py")
if ($LASTEXITCODE -ne 0) { throw "Icon generation failed" }

Write-Host "==> Cleaning previous build output" -ForegroundColor Cyan
foreach ($path in @($Dist, $Build)) {
    if (Test-Path $path) { Remove-Item -Recurse -Force $path }
}

Write-Host "==> Running PyInstaller (this takes a minute)" -ForegroundColor Cyan
Push-Location $Root
try {
    & $Python -m PyInstaller --noconfirm --clean (Join-Path $Root "packaging\DeskX.spec")
    if ($LASTEXITCODE -ne 0) { throw "PyInstaller failed" }
}
finally {
    Pop-Location
}

$AppDir = Join-Path $Dist "DeskX"
if (-not (Test-Path (Join-Path $AppDir "DeskX.exe"))) {
    throw "Expected DeskX.exe was not produced"
}

Write-Host "==> Adding end-user readme" -ForegroundColor Cyan
Copy-Item (Join-Path $Root "packaging\README-FIRST.txt") $AppDir -Force

Write-Host "==> Packing $Zip" -ForegroundColor Cyan
if (-not (Test-Path $Release)) { New-Item -ItemType Directory -Path $Release | Out-Null }
if (Test-Path $Zip) { Remove-Item -Force $Zip }
Compress-Archive -Path $AppDir -DestinationPath $Zip -CompressionLevel Optimal

$SizeMb = [math]::Round((Get-Item $Zip).Length / 1MB, 1)
Write-Host ""
Write-Host "Done. $Zip ($SizeMb MB)" -ForegroundColor Green

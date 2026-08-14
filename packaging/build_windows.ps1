<#
.SYNOPSIS
    Build the distributable Windows package for DeskX (GUI + CLI).

.DESCRIPTION
    Regenerates the app icon, builds DeskX.exe (GUI) and deskx.exe (CLI),
    drops the end-user readme into the bundle, and zips the result to
    release/DeskX-Windows.zip.

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

Write-Host "==> Building GUI (DeskX.exe)" -ForegroundColor Cyan
Push-Location $Root
try {
    & $Python -m PyInstaller --noconfirm --clean (Join-Path $Root "packaging\DeskX.spec")
    if ($LASTEXITCODE -ne 0) { throw "GUI PyInstaller failed" }

    Write-Host "==> Building CLI (deskx.exe)" -ForegroundColor Cyan
    & $Python -m PyInstaller --noconfirm --clean (Join-Path $Root "packaging\DeskX-CLI.spec")
    if ($LASTEXITCODE -ne 0) { throw "CLI PyInstaller failed" }
}
finally {
    Pop-Location
}

$AppDir = Join-Path $Dist "DeskX"
if (-not (Test-Path (Join-Path $AppDir "DeskX.exe"))) {
    throw "Expected DeskX.exe was not produced"
}

$CliExe = Join-Path $Dist "deskx.exe"
if (-not (Test-Path $CliExe)) {
    throw "Expected deskx.exe was not produced"
}
Copy-Item $CliExe $AppDir -Force

Write-Host "==> Adding end-user readme" -ForegroundColor Cyan
Copy-Item (Join-Path $Root "packaging\README-FIRST.txt") $AppDir -Force

Write-Host "==> Packing $Zip" -ForegroundColor Cyan
if (-not (Test-Path $Release)) { New-Item -ItemType Directory -Path $Release | Out-Null }
if (Test-Path $Zip) { Remove-Item -Force $Zip }
Compress-Archive -Path $AppDir -DestinationPath $Zip -CompressionLevel Optimal

$SizeMb = [math]::Round((Get-Item $Zip).Length / 1MB, 1)
Write-Host ""
Write-Host "Done. $Zip ($SizeMb MB)" -ForegroundColor Green
Write-Host "  GUI: DeskX.exe"
Write-Host "  CLI: deskx.exe  (open a terminal in this folder and run: .\deskx.exe --help)"

# Safe additive TF2 installation of NEW J2ME profiles only.
# Windows PowerShell 5.1+, read-only unless -Apply was provided.
# Usage:
# powershell.exe -NoProfile -ExecutionPolicy Bypass -File "<repo>\scripts\install-additional-jars.ps1" -Stage "<repo>\out\additional-jars-01" -Tf2Root "F:\"
# Repeat with -Apply only after the dry-run reports PREFLIGHT_OK.
param(
    [Parameter(Mandatory=$true)][string]$Stage,
    [Parameter(Mandatory=$true)][string]$Tf2Root,
    [switch]$Apply
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

if (-not (Test-Path -LiteralPath $Stage -PathType Container)) {
    throw "MISSING STAGING FOLDER: $Stage"
}
if (-not (Test-Path -LiteralPath $Tf2Root -PathType Container)) {
    throw "MISSING TF2 ROOT: $Tf2Root"
}

$planPath = Join-Path $Stage '.host-only\install-plan.json'
if (-not (Test-Path -LiteralPath $planPath -PathType Leaf)) {
    throw "MISSING INSTALL PLAN: $planPath"
}
$plan = Get-Content -LiteralPath $planPath -Raw | ConvertFrom-Json
if ($plan.schema_version -ne 1 -or $plan.purpose -ne 'additive-only') {
    throw "Unsupported install plan"
}
$files = @($plan.files)
$games = @($plan.games)
if ($games.Count -eq 0 -or $files.Count -ne (4 * $games.Count)) {
    throw "Invalid staged file count for selected games"
}

# Verify this really is the existing TF2 universal launcher installation.
$required = @(
    'J2ME\universal-v1\dispatch.sh'
    'J2ME\universal-v1\options\bounce.opt'
    'J2ME\universal-v1\options\diamond-rush.opt'
    'Roms\PORTS\J2ME_bounce.sh'
    'Roms\PORTS\J2ME_diamond_rush.sh'
    'Roms\JAVA\Bounce.jar'
    'Roms\JAVA\Diamond Rush.jar'
    'J2ME\core\freej2me_plus_exit_test_libretro.so'
    'J2ME\test-system\freej2me_plus_runtime\linux-arm\bin\freej2me_plus-lr.jar'
)
foreach ($relative in $required) {
    $target = Join-Path $Tf2Root $relative
    if (-not (Test-Path -LiteralPath $target -PathType Leaf)) {
        throw "This does not look like the verified TF2: MISSING $target"
    }
}

$seen = @{}
$copyPlan = @()
foreach ($entry in $files) {
    $rel = [string]$entry.path
    $expect = [string]$entry.sha256

    # Permit only these very specific targets; never ROMs, the dispatcher or TF1.
    if ($rel -notmatch '^(?:J2ME/universal-v1/(?:options|launcher-config|config/FreeJ2ME-Plus)/[A-Za-z0-9 _().+-]+\.opt|Roms/PORTS/J2ME_[a-z0-9_-]+\.sh)$') {
        throw "UNSAFE DESTINATION IN PLAN: $rel"
    }
    if ($expect -notmatch '^[0-9a-fA-F]{64}$') {
        throw "INVALID EXPECTED SHA256: $rel"
    }
    if ($seen.ContainsKey($rel.ToLowerInvariant())) {
        throw "DUPLICATE TARGET IN PLAN: $rel"
    }
    $seen[$rel.ToLowerInvariant()] = $true

    $windowsRel = $rel.Replace('/', '\')
    $from = Join-Path $Stage $windowsRel
    $to = Join-Path $Tf2Root $windowsRel

    if (-not (Test-Path -LiteralPath $from -PathType Leaf)) {
        throw "MISSING SOURCE: $from"
    }
    if (Test-Path -LiteralPath $to) {
        throw "REFUSING TO OVERWRITE EXISTING FILE: $to"
    }
    $actualHash = (Get-FileHash -LiteralPath $from -Algorithm SHA256).Hash
    if ($actualHash -ne $expect) {
        throw "SOURCE HASH MISMATCH: $rel"
    }

    $copyPlan += [pscustomobject]@{ Relative=$rel; From=$from; To=$to; SHA256=$expect }
}

Write-Host "PREFLIGHT_OK - $($games.Count) new games, $($copyPlan.Count) new files." -ForegroundColor Green
foreach ($game in $games) {
    Write-Host "NEW: $($game.rom_file) [fallback $($game.resolution), sound $($game.sound)]"
}

if (-not $Apply) {
    Write-Host 'DRY_RUN_OK - No files copied. Re-run with -Apply after reviewing the list.' -ForegroundColor Green
    exit 0
}

foreach ($item in $copyPlan) {
    $parent = Split-Path -Path $item.To -Parent
    [System.IO.Directory]::CreateDirectory($parent) | Out-Null
    # Strictly non-overwriting. If anything appeared since preflight, fail.
    [System.IO.File]::Copy($item.From, $item.To, $false)
    $newHash = (Get-FileHash -LiteralPath $item.To -Algorithm SHA256).Hash
    if ($newHash -ne $item.SHA256) {
        throw "DESTINATION HASH MISMATCH: $($item.Relative) - do not launch until checked"
    }
    Write-Host "VERIFIED: $($item.Relative)" -ForegroundColor Green
}

Write-Host 'ADDITIVE_COPY_OK' -ForegroundColor Green
Write-Host 'Safely eject TF2 after confirming completion. No stable files were replaced.'

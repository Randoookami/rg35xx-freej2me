# Incremental TF2 installation: NEW J2ME files only.
# PowerShell 5.1+. Default is a read-only dry-run. -Apply is explicit.
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
    throw 'Unsupported installation plan'
}
$games = @($plan.games)
$files = @($plan.files)
if ($games.Count -eq 0 -or $files.Count -ne (4 * $games.Count)) {
    throw 'Invalid game count or file count'
}

# Identify the installed and previously tested TF2 without changing it.
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
foreach ($rel in $required) {
    $path = Join-Path $Tf2Root $rel
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
        throw "TF2 identity check FAILED: $path"
    }
}

# Build an EXACT allowlist from the games in the signed-off install plan.
# This prevents an unexpected destination such as ROMs, saves or dispatch.sh.
$allowed = @{}
foreach ($game in $games) {
    $name = [string]$game.rom_file
    $id = [string]$game.id

    if ($name -cnotmatch '^[A-Za-z0-9 _().+-]+\.jar$') {
        throw "Invalid ROM filename in plan: $name"
    }
    if ($id -cnotmatch '^auto-[a-z0-9-]+-[0-9a-f]{8}$') {
        throw "Invalid new profile ID: $id"
    }
    $jar = Join-Path $Tf2Root ('Roms\JAVA\' + $name)
    if (-not (Test-Path -LiteralPath $jar -PathType Leaf)) {
        throw "NEW JAR MISSING ON TF2: $jar"
    }

    $stem = [System.IO.Path]::GetFileNameWithoutExtension($name)
    $launcherId = $id.Replace('-', '_')
    $paths = @(
        ('J2ME/universal-v1/options/' + $id + '.opt')
        ('J2ME/universal-v1/launcher-config/' + $id + '.cfg')
        ('J2ME/universal-v1/config/FreeJ2ME-Plus/' + $stem + '.opt')
        ('Roms/PORTS/J2ME_' + $launcherId + '.sh')
    )
    foreach ($rel in $paths) {
        $key = $rel.ToLowerInvariant()
        if ($allowed.ContainsKey($key)) {
            throw "Duplicate generated destination: $rel"
        }
        $allowed[$key] = $true
    }
}

$seen = @{}
$copyPlan = @()
foreach ($entry in $files) {
    $rel = [string]$entry.path
    $expectedHash = [string]$entry.sha256
    $key = $rel.ToLowerInvariant()

    if (-not $allowed.ContainsKey($key)) {
        throw "UNEXPECTED DESTINATION: $rel"
    }
    if ($seen.ContainsKey($key)) {
        throw "DUPLICATE DESTINATION: $rel"
    }
    if ($expectedHash -cnotmatch '^[0-9a-fA-F]{64}$') {
        throw "Invalid SHA256 in plan: $rel"
    }
    $seen[$key] = $true

    $windowsRel = $rel.Replace('/', '\')
    $source = Join-Path $Stage $windowsRel
    $target = Join-Path $Tf2Root $windowsRel

    if (-not (Test-Path -LiteralPath $source -PathType Leaf)) {
        throw "MISSING SOURCE: $source"
    }
    if (Test-Path -LiteralPath $target) {
        throw "REFUSING OVERWRITE: $target"
    }

    $sourceHash = (Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash
    if ($sourceHash -ine $expectedHash) {
        throw "SOURCE SHA256 MISMATCH: $rel"
    }
    $copyPlan += [pscustomobject]@{
        Relative = $rel
        Source = $source
        Target = $target
        SHA256 = $expectedHash
    }
}

if ($seen.Count -ne $allowed.Count) {
    throw "Incomplete file plan (expected $($allowed.Count), found $($seen.Count))"
}

Write-Host "PREFLIGHT_OK: $($games.Count) new games, $($copyPlan.Count) new files" -ForegroundColor Green
foreach ($game in $games) {
    Write-Host "NEW: $($game.rom_file) / $($game.resolution) / sound $($game.sound)"
}

if (-not $Apply) {
    Write-Host 'DRY_RUN_OK: nothing written to TF2' -ForegroundColor Green
    exit 0
}

foreach ($item in $copyPlan) {
    $parent = Split-Path -Path $item.Target -Parent
    [System.IO.Directory]::CreateDirectory($parent) | Out-Null
    # Atomic fail-on-exists semantics: never replace an existing file.
    [System.IO.File]::Copy($item.Source, $item.Target, $false)
    $actual = (Get-FileHash -LiteralPath $item.Target -Algorithm SHA256).Hash
    if ($actual -ine $item.SHA256) {
        throw "DESTINATION SHA256 MISMATCH: $($item.Relative)"
    }
    Write-Host "VERIFIED: $($item.Relative)" -ForegroundColor Green
}
Write-Host 'ADDITIVE_COPY_OK' -ForegroundColor Green

# One-way, never-deleting, never-overwriting backup of the data root's append-only layers.
# Copies only files that don't yet exist in the destination (raw/cache/docs/packs are append-only).
# Run nightly by the Windows scheduled task "PN data backup".

$ErrorActionPreference = "Stop"
$root = [Environment]::GetEnvironmentVariable("PN_DATA_ROOT", "User")
if (-not $root) { $root = Join-Path $env:USERPROFILE "pn-data" }
$dest = Join-Path $env:USERPROFILE "OneDrive\pn-data-backup"
$log = Join-Path $root "tmp\backup.log"

foreach ($layer in "raw", "cache", "docs", "packs") {
    $src = Join-Path $root $layer
    if (-not (Test-Path $src)) { continue }
    # /E subfolders · /XC /XN /XO skip any file that already exists (never overwrite) · no /MIR (never delete)
    robocopy $src (Join-Path $dest $layer) /E /XC /XN /XO /R:1 /W:5 /NP /NDL /LOG+:$log | Out-Null
    if ($LASTEXITCODE -ge 8) { throw "robocopy failed for $layer (exit $LASTEXITCODE); see $log" }
}

# Monthly MDSP crash refresh: re-pulls the trailing 9 complete months of all 8 ACRS tables through the
# tableau_public connector and runs the pn intake checks. Unchanged months add no snapshot.
# Run on the 7th of each month by the Windows scheduled task "PN MDSP monthly" (ops/register_mdsp_monthly.ps1).
#
# It changes catalog/manifests/raw_manifest.jsonl in the repo working tree but never commits or pushes;
# review and commit the new manifest lines yourself. Exit code is pn's (1 if any month failed); see the log.

$ErrorActionPreference = "Stop"
$root = [Environment]::GetEnvironmentVariable("PN_DATA_ROOT", "User")
if (-not $root) { $root = Join-Path $env:USERPROFILE "pn-data" }
$env:PN_DATA_ROOT = $root
$env:PYTHONIOENCODING = "utf-8"
$env:PATH = "$env:APPDATA\Python\Python313\Scripts;$env:USERPROFILE\.local\bin;$env:PATH"
$repo = Split-Path $PSScriptRoot -Parent
$log = Join-Path $root "tmp\mdsp_monthly.log"

Set-Location $repo
"==== $(Get-Date -Format s) pn fetch mdsp_acrs (trailing months)" | Out-File $log -Append -Encoding utf8
# pn prints UTF-8; capture it as text so the log stays readable
$out = & uv run pn fetch mdsp_acrs 2>&1 | ForEach-Object { "$_" }
$code = $LASTEXITCODE
$out | Out-File $log -Append -Encoding utf8
"==== $(Get-Date -Format s) exit $code" | Out-File $log -Append -Encoding utf8
exit $code

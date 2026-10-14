# Registers (or updates) the scheduled task "PN MDSP monthly": 6:00 AM on the 7th of every month, as the
# current user, only when logged on (same as "PN data backup"); runs late if the PC was off at that time.
$ErrorActionPreference = "Stop"
$name = "PN MDSP monthly"
$script = Join-Path $PSScriptRoot "mdsp_monthly.ps1"
$run = "powershell.exe -NoProfile -NonInteractive -ExecutionPolicy Bypass -File `"$script`""
# New-ScheduledTaskTrigger has no monthly trigger, so create the task with schtasks, then set its options.
schtasks.exe /Create /F /TN $name /TR $run /SC MONTHLY /D 7 /ST 06:00 /IT | Out-Null
if ($LASTEXITCODE -ne 0) { throw "schtasks failed ($LASTEXITCODE)" }
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -ExecutionTimeLimit (New-TimeSpan -Hours 3)
Set-ScheduledTask -TaskName $name -Settings $settings | Out-Null
Get-ScheduledTask -TaskName $name | Get-ScheduledTaskInfo | Select-Object TaskName, NextRunTime

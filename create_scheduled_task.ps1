# create_scheduled_task.ps1
$Action = New-ScheduledTaskAction `
    -Execute "C:\path\to\startup-automation\venv\Scripts\python.exe" `
    -Argument "main.py" `
    -WorkingDirectory "C:\path\to\startup-automation"

$Trigger = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME

$Settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 10)

$Principal = New-ScheduledTaskPrincipal `
    -UserId $env:USERNAME `
    -RunLevel Highest

Register-ScheduledTask `
    -TaskName "StartupAutomation" `
    -Action $Action `
    -Trigger $Trigger `
    -Settings $Settings `
    -Principal $Principal `
    -Description "Automated startup: VPN, browsers, apps"

Write-Host "Scheduled task created successfully!" -ForegroundColor Green

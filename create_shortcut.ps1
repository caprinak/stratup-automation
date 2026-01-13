$WshShell = New-Object -ComObject WScript.Shell
$ShortcutPath = "$PSScriptRoot\Startup_Launcher.lnk"
$Shortcut = $WshShell.CreateShortcut($ShortcutPath)
$Shortcut.TargetPath = "wscript.exe"
$Shortcut.Arguments = "`"$PSScriptRoot\start_launcher.vbs`""
$Shortcut.WorkingDirectory = "$PSScriptRoot"
$Shortcut.IconLocation = "$PSScriptRoot\venv\Scripts\python.exe,0"
$Shortcut.Description = "Launch Startup Automation Tray"
$Shortcut.Save()
Write-Host "Shortcut created at: $ShortcutPath"

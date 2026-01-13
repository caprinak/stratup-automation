Set WshShell = CreateObject("WScript.Shell")
' Get the directory of the script
strPath = Left(WScript.ScriptFullName, InStrRev(WScript.ScriptFullName, "\"))
' Run the launcher using the virtual environment python, hidden window
WshShell.Run """" & strPath & "venv\Scripts\pythonw.exe"" """ & strPath & "launcher.py""", 0, False

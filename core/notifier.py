"""
Windows toast notifications
"""
import subprocess
from typing import Optional
from core.logger import get_logger


class Notifier:
    """Send Windows toast notifications."""
    
    def __init__(self, enabled: bool = True):
        self.enabled = enabled
        self.logger = get_logger()
    
    def notify(
        self,
        title: str,
        message: str,
        icon: str = "info"  # info, warning, error
    ):
        """Send a toast notification using PowerShell."""
        if not self.enabled:
            return
        
        try:
            # PowerShell toast notification
            ps_script = f'''
            [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
            [Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, ContentType = WindowsRuntime] | Out-Null

            $template = @"
            <toast>
                <visual>
                    <binding template="ToastText02">
                        <text id="1">{title}</text>
                        <text id="2">{message}</text>
                    </binding>
                </visual>
            </toast>
"@

            $xml = New-Object Windows.Data.Xml.Dom.XmlDocument
            $xml.LoadXml($template)
            $toast = New-Object Windows.UI.Notifications.ToastNotification $xml
            [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("Startup Automation").Show($toast)
            '''
            
            subprocess.run(
                ["powershell", "-Command", ps_script],
                capture_output=True,
                check=False
            )
            
        except Exception as e:
            self.logger.warning(f"Failed to send notification: {e}")
    
    def success(self, message: str):
        """Send success notification."""
        self.notify("✅ Startup Complete", message)
    
    def error(self, message: str):
        """Send error notification."""
        self.notify("❌ Startup Error", message)
    
    def warning(self, message: str):
        """Send warning notification."""
        self.notify("⚠️ Startup Warning", message)

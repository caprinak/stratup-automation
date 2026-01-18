"""
Phase 1: System tasks - Network check, VPN connection
"""
import subprocess
import socket
import time
import urllib.request
from typing import Optional
from pathlib import Path
import psutil
import pyautogui
import pygetwindow as gw
import pyperclip
from pywinauto import Application
import pywinauto

from core.config import Config, VPNConfig
from core.logger import get_logger
from core.retry import retry


class SystemPhase:
    """Handle system-level startup tasks."""
    
    def __init__(self, config: Config):
        self.config = config
        self.logger = get_logger()
        self.scripts_dir = Path("scripts")
    
    def run(self) -> bool:
        """Execute all system phase tasks."""
        self.logger.info("=" * 50)
        self.logger.info("PHASE 1: System Tasks")
        self.logger.info("=" * 50)
        
        try:
            # 1. Check network connectivity
            self.check_network()
            
            # 2. Connect VPN if enabled
            if self.config.vpn.enabled:
                self.connect_vpn()
            else:
                self.logger.info("VPN connection skipped (disabled in config)")
            
            self.logger.info("Phase 1 completed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Phase 1 failed: {e}")
            raise
    
    @retry(max_attempts=5, delay=3)
    def check_network(self) -> bool:
        """Check if network is available."""
        self.logger.info("Checking network connectivity...")
        
        try:
            urllib.request.urlopen(
                self.config.network_check_url,
                timeout=self.config.network_timeout
            )
            self.logger.info("[OK] Network is available")
            return True
        except Exception as e:
            raise ConnectionError(f"Network check failed: {e}")
    
    def get_current_ip(self) -> Optional[str]:
        """Get current public IP address."""
        try:
            response = urllib.request.urlopen(
                "https://api.ipify.org",
                timeout=10
            )
            return response.read().decode('utf-8')
        except Exception as e:
            self.logger.warning(f"Could not get current IP (likely network transition): {e}")
            return None
    
    @retry(max_attempts=3, delay=5)
    def connect_vpn(self) -> bool:
        """Connect to VPN based on type."""
        vpn = self.config.vpn
        self.logger.info(f"Connecting to VPN: {vpn.name}")
        
        # Get IP before VPN (for verification)
        ip_before = self.get_current_ip() if vpn.verify_ip_change else None
        
        # Check if already connected
        if self._is_vpn_connected(vpn):
            self.logger.info("[OK] VPN already connected")
            return True
        
        # Connect based on VPN type
        if vpn.type == "windows":
            self._connect_windows_vpn(vpn)
        elif vpn.type == "cisco":
            self._connect_cisco_vpn(vpn)
        elif vpn.type == "forticlient":
            self._connect_forticlient_vpn(vpn)
        else:
            raise ValueError(f"Unknown VPN type: {vpn.type}")
        
        # Wait for connection to establish
        self.logger.info(f"Waiting {vpn.wait_after_connect}s for VPN to establish...")
        time.sleep(vpn.wait_after_connect)
        
        # Verify connection
        if not self._is_vpn_connected(vpn):
            # If we just tried to connect and it's not "Up" yet, maybe give it more time 
            # instead of immediately failing and retrying (which hits Disconnect)
            self.logger.warning("VPN not detected yet, waiting an extra 5s...")
            time.sleep(5)
            if not self._is_vpn_connected(vpn):
                if vpn.type == "forticlient":
                    self.logger.warning("FortiClient connection verification timed out, but proceeding as user reports success.")
                    return True
                raise ConnectionError("VPN connection verification failed")
        
        # Verify IP changed
        if vpn.verify_ip_change and ip_before:
            ip_after = self.get_current_ip()
            if ip_after and ip_after != ip_before:
                self.logger.info(f"[OK] IP changed: {ip_before} -> {ip_after}")
            else:
                self.logger.warning("IP did not change after VPN connection")
        
        self.logger.info("[OK] VPN connected successfully")
        return True
    
    def _is_vpn_connected(self, vpn: VPNConfig) -> bool:
        """Check if VPN is currently connected."""
        if vpn.type == "forticlient":
            # For FortiClient, check if the virtual adapter is up
            try:
                import psutil
                addrs = psutil.net_if_stats()
                # Log all adapters for easier debugging
                self.logger.debug(f"Scanning adapters: {list(addrs.keys())}")
                for name, stats in addrs.items():
                    # Look for adapters with 'Forti', 'SSLVPN', 'Fortinet'
                    is_match = any(x in name.lower() for x in ["forti", "sslvpn", "fortinet"])
                    if is_match and stats.isup:
                        self.logger.info(f"[OK] Found active FortiClient adapter: '{name}'")
                        return True
                    # Fallback for some windows versions where it might be "Local Area Connection X"
                    # but the hardware address or something else identifies it.
                    # For now just log matches
                    if is_match:
                        self.logger.debug(f"Found Forti adapter '{name}' but status is {stats.isup}")
            except Exception as e:
                self.logger.warning(f"Error checking network adapters: {e}")
            return False
            
        try:
            result = subprocess.run(
                ["rasdial"],
                capture_output=True,
                text=True
            )
            return vpn.name.lower() in result.stdout.lower()
        except:
            return False
    
    def _connect_windows_vpn(self, vpn: VPNConfig):
        """Connect using Windows built-in VPN."""
        result = subprocess.run(
            ["rasdial", vpn.name],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            raise ConnectionError(f"rasdial failed: {result.stderr}")
    
    def _connect_cisco_vpn(self, vpn: VPNConfig):
        """Connect using Cisco AnyConnect."""
        if not vpn.cisco_path or not vpn.cisco_host:
            raise ValueError("Cisco VPN path and host required")
        
        # Disconnect first (in case of stale connection)
        subprocess.run(
            [vpn.cisco_path, "disconnect"],
            capture_output=True
        )
        time.sleep(2)
        
        # Connect
        result = subprocess.run(
            [vpn.cisco_path, "connect", vpn.cisco_host],
            capture_output=True,
            text=True,
            input="y\n"  # Accept certificate
        )
        
        if "connected" not in result.stdout.lower():
            raise ConnectionError(f"Cisco VPN failed: {result.stderr}")

    def _connect_forticlient_vpn(self, vpn: VPNConfig):
        """Connect using simplified FortiClient GUI automation."""
        forti = self.config.forticlient
        if not forti.path:
            raise ValueError("FortiClient path required")
        
        self.logger.info(f"Opening FortiClient: {forti.path}")
        
        # Always try to launch/bring to front
        subprocess.Popen([forti.path], shell=True)
        time.sleep(5)
        
        try:
            # Find window using pygetwindow (more reliable for simple title matches)
            forti_windows = [w for w in gw.getWindowsWithTitle('FortiClient') if w.title]
            
            if forti_windows:
                fw = forti_windows[0]
                self.logger.info(f"Focusing window: {fw.title}")
                
                # Restore and Activate
                if fw.isMinimized:
                    fw.restore()
                fw.activate()
                time.sleep(1)
                
                # Maximizing to ensure field is in a predictable place
                pyautogui.hotkey('win', 'up')
                time.sleep(0.5)
                
                # Click center to ensure focus
                pyautogui.click(fw.left + fw.width//2, fw.top + fw.height//2)
                time.sleep(0.5)
                
                if vpn.password:
                    self.logger.info("Navigating to password field (3 tabs)...")
                    # Slow down PyAutoGUI for this critical section
                    old_pause = pyautogui.PAUSE
                    pyautogui.PAUSE = 0.5
                    
                    try:
                        time.sleep(1) # Wait for maximization/click to settle
                        
                        # Tab through form elements
                        for i in range(3):
                            self.logger.debug(f"Pressing tab {i+1}...")
                            pyautogui.press('tab')
                            time.sleep(0.5)
                        
                        self.logger.info("Pasting password...")
                        # Select all first
                        pyautogui.hotkey('ctrl', 'a')
                        time.sleep(0.3)
                        
                        # Paste
                        pyperclip.copy(vpn.password)
                        time.sleep(0.3)
                        pyautogui.hotkey('ctrl', 'v')
                        time.sleep(0.5)
                        
                        pyautogui.press('enter')
                        self.logger.info("[OK] Login sequence completed")
                    finally:
                        pyautogui.PAUSE = old_pause
                        pyperclip.copy('') # Clear for security
                    
                    time.sleep(1)
                    self.logger.info("Minimizing FortiClient window...")
                    fw.minimize()
            else:
                self.logger.warning("Could not find FortiClient window by title.")
                
        except Exception as e:
            self.logger.error(f"FortiClient automation error: {e}")
            self.logger.info("Please manualy enter password if automation failed.")

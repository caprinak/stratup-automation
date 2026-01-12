"""
Phase 1: System tasks - Network check, VPN connection
"""
import subprocess
import socket
import time
import urllib.request
from typing import Optional
from pathlib import Path

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
            self.logger.info("✓ Network is available")
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
        except:
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
            self.logger.info("✓ VPN already connected")
            return True
        
        # Connect based on VPN type
        if vpn.type == "windows":
            self._connect_windows_vpn(vpn)
        elif vpn.type == "cisco":
            self._connect_cisco_vpn(vpn)
        else:
            raise ValueError(f"Unknown VPN type: {vpn.type}")
        
        # Wait for connection to establish
        self.logger.info(f"Waiting {vpn.wait_after_connect}s for VPN to establish...")
        time.sleep(vpn.wait_after_connect)
        
        # Verify connection
        if not self._is_vpn_connected(vpn):
            raise ConnectionError("VPN connection verification failed")
        
        # Verify IP changed
        if vpn.verify_ip_change and ip_before:
            ip_after = self.get_current_ip()
            if ip_after and ip_after != ip_before:
                self.logger.info(f"✓ IP changed: {ip_before} → {ip_after}")
            else:
                self.logger.warning("IP did not change after VPN connection")
        
        self.logger.info("✓ VPN connected successfully")
        return True
    
    def _is_vpn_connected(self, vpn: VPNConfig) -> bool:
        """Check if VPN is currently connected."""
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

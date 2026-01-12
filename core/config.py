"""
Configuration loader and validator
"""
from dataclasses import dataclass, field
from typing import Optional, List, Dict
from pathlib import Path
import yaml


@dataclass
class VPNConfig:
    enabled: bool = True
    name: str = ""
    type: str = "windows"
    wait_after_connect: int = 8
    verify_ip_change: bool = True
    cisco_path: Optional[str] = None
    cisco_host: Optional[str] = None


@dataclass
class BrowserWindowConfig:
    width: int = 1920
    height: int = 1080
    maximized: bool = True


@dataclass
class BrowserURL:
    url: str
    wait_for: str = "load"


@dataclass
class BrowserConfig:
    enabled: bool = True
    browser_type: str = "chromium"
    profile_dir: str = ""
    startup_urls: List[BrowserURL] = field(default_factory=list)
    window: BrowserWindowConfig = field(default_factory=BrowserWindowConfig)


@dataclass
class FolderConfig:
    path: str
    explorer_view: str = "details"


@dataclass
class IDEConfig:
    name: str
    path: str
    project: Optional[str] = None
    wait_seconds: int = 5


@dataclass
class Config:
    log_level: str = "INFO"
    log_dir: str = "logs"
    max_retries: int = 3
    retry_delay: int = 5
    parallel_browsers: bool = False
    network_check_url: str = "https://www.google.com"
    network_timeout: int = 10
    vpn: VPNConfig = field(default_factory=VPNConfig)
    folders: List[FolderConfig] = field(default_factory=list)
    ides: List[IDEConfig] = field(default_factory=list)
    browsers: Dict[str, BrowserConfig] = field(default_factory=dict)
    notifications_enabled: bool = True


def load_config(config_path: str = "config.yaml") -> Config:
    """Load and parse configuration from YAML file."""
    path = Path(config_path)
    
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    
    with open(path, 'r', encoding='utf-8') as f:
        raw = yaml.safe_load(f)
    
    # Parse into dataclasses
    config = Config()
    
    # General settings
    general = raw.get('general', {})
    config.log_level = general.get('log_level', 'INFO')
    config.log_dir = general.get('log_dir', 'logs')
    config.max_retries = general.get('max_retries', 3)
    config.retry_delay = general.get('retry_delay', 5)
    config.parallel_browsers = general.get('parallel_browsers', False)
    
    # Network
    network = raw.get('network', {})
    config.network_check_url = network.get('check_url', 'https://www.google.com')
    config.network_timeout = network.get('timeout_seconds', 10)
    
    # VPN
    vpn_raw = raw.get('vpn', {})
    config.vpn = VPNConfig(
        enabled=vpn_raw.get('enabled', True),
        name=vpn_raw.get('name', ''),
        type=vpn_raw.get('type', 'windows'),
        wait_after_connect=vpn_raw.get('wait_after_connect', 8),
        verify_ip_change=vpn_raw.get('verify_ip_change', True),
        cisco_path=vpn_raw.get('cisco', {}).get('path'),
        cisco_host=vpn_raw.get('cisco', {}).get('host'),
    )
    
    # Folders
    for folder in raw.get('folders', []):
        config.folders.append(FolderConfig(
            path=folder.get('path', ''),
            explorer_view=folder.get('explorer_view', 'details')
        ))
    
    # IDEs
    for ide in raw.get('ides', []):
        config.ides.append(IDEConfig(
            name=ide.get('name', ''),
            path=ide.get('path', ''),
            project=ide.get('project'),
            wait_seconds=ide.get('wait_seconds', 5)
        ))
    
    # Browsers
    for name, browser in raw.get('browsers', {}).items():
        urls = []
        for url_config in browser.get('startup_urls', []):
            urls.append(BrowserURL(
                url=url_config.get('url', ''),
                wait_for=url_config.get('wait_for', 'load')
            ))
        
        window_raw = browser.get('window', {})
        window = BrowserWindowConfig(
            width=window_raw.get('width', 1920),
            height=window_raw.get('height', 1080),
            maximized=window_raw.get('maximized', True)
        )
        
        config.browsers[name] = BrowserConfig(
            enabled=browser.get('enabled', True),
            browser_type=browser.get('browser_type', 'chromium'),
            profile_dir=browser.get('profile_dir', ''),
            startup_urls=urls,
            window=window
        )
    
    # Notifications
    notifications = raw.get('notifications', {})
    config.notifications_enabled = notifications.get('enabled', True)
    
    return config

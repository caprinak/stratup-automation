"""
Configuration loader and validator using Pydantic
"""
from pathlib import Path
from typing import Optional, List, Dict, Literal
from pydantic import BaseModel, Field, field_validator, model_validator
import yaml
import os
from dotenv import load_dotenv
from core.vault import get_vpn_password


class VPNConfig(BaseModel):
    enabled: bool = True
    name: str = ""
    type: Literal["windows", "cisco", "nordvpn", "forticlient"] = "windows"
    wait_after_connect: int = Field(default=8, ge=1, le=60)
    verify_ip_change: bool = True
    password: Optional[str] = Field(default=None, exclude=True)
    cisco_path: Optional[str] = None
    cisco_host: Optional[str] = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str, info) -> str:
        if info.data.get("enabled") and not v:
            raise ValueError("VPN name is required when VPN is enabled")
        return v


class FortiClientConfig(BaseModel):
    path: str = Field(default="C:/Program Files/Fortinet/FortiClient/FortiClient.exe")

    @field_validator("path")
    @classmethod
    def validate_path(cls, v: str) -> str:
        if not v:
            raise ValueError("FortiClient path cannot be empty")
        return v


class BrowserWindowConfig(BaseModel):
    width: int = Field(default=1920, ge=800, le=7680)
    height: int = Field(default=1080, ge=600, le=4320)
    maximized: bool = True


class BrowserURL(BaseModel):
    url: str
    wait_for: Literal["load", "domcontentloaded", "networkidle", "commit"] = "load"

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        if not v.startswith(("http://", "https://")):
            raise ValueError(f"URL must start with http:// or https://: {v}")
        return v


class BrowserConfig(BaseModel):
    enabled: bool = True
    browser_type: Literal["chromium", "firefox", "webkit"] = "chromium"
    profile_dir: str = ""
    startup_urls: List[BrowserURL] = Field(default_factory=list)
    window: BrowserWindowConfig = Field(default_factory=BrowserWindowConfig)

    @field_validator("profile_dir")
    @classmethod
    def validate_profile_dir(cls, v: str, info) -> str:
        if v and info.data.get("enabled"):
            profile_path = Path(v)
            if not profile_path.exists():
                try:
                    profile_path.mkdir(parents=True, exist_ok=True)
                except Exception as e:
                    raise ValueError(f"Cannot create profile directory {v}: {e}")
        return v


class FolderConfig(BaseModel):
    path: str
    explorer_view: Literal["details", "list", "icons", "tiles", "content"] = "details"

    @field_validator("path")
    @classmethod
    def validate_path(cls, v: str) -> str:
        if not v:
            raise ValueError("Folder path cannot be empty")
        return v


class IDEConfig(BaseModel):
    name: str = Field(min_length=1)
    path: str = Field(min_length=1)
    project: Optional[str] = None
    wait_seconds: int = Field(default=5, ge=0, le=60)

    @field_validator("path")
    @classmethod
    def validate_path(cls, v: str) -> str:
        if not v:
            raise ValueError("IDE path cannot be empty")
        return v


class HealthCheckConfig(BaseModel):
    method: Literal["window_title", "port", "process", "none"] = "none"
    pattern: str = ""
    timeout: int = Field(default=10, ge=1, le=60)
    retries: int = Field(default=2, ge=0, le=5)

    @model_validator(mode='after')
    def validate_pattern_required(self):
        if self.method != "none" and not self.pattern:
            raise ValueError(f"Pattern is required when health_check method is '{self.method}'")
        return self


class GeneralAppConfig(BaseModel):
    name: str = Field(min_length=1)
    path: str = Field(min_length=1)
    args: List[str] = Field(default_factory=list)
    wait_seconds: int = Field(default=2, ge=0, le=60)
    depends_on: List[str] = Field(default_factory=list, description="List of app names this app depends on")
    enabled: bool = True
    conditions: Optional[Dict[str, str]] = Field(default=None, description="Conditions for launching this app")
    health_check: HealthCheckConfig = Field(default_factory=HealthCheckConfig)

    @field_validator("path")
    @classmethod
    def validate_path(cls, v: str) -> str:
        if not v:
            raise ValueError("App path cannot be empty")
        return v


class NotificationsConfig(BaseModel):
    enabled: bool = True
    on_success: bool = True
    on_failure: bool = True
    sound: bool = True


class Config(BaseModel):
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    log_dir: str = Field(default="logs", min_length=1)
    max_retries: int = Field(default=3, ge=1, le=10)
    retry_delay: int = Field(default=5, ge=1, le=60)
    parallel_browsers: bool = False
    network_check_url: str = Field(default="https://www.google.com", min_length=1)
    network_timeout: int = Field(default=10, ge=1, le=60)
    vpn: VPNConfig = Field(default_factory=VPNConfig)
    folders: List[FolderConfig] = Field(default_factory=list)
    ides: List[IDEConfig] = Field(default_factory=list)
    apps: List[GeneralAppConfig] = Field(default_factory=list)
    browsers: Dict[str, BrowserConfig] = Field(default_factory=dict)
    forticlient: FortiClientConfig = Field(default_factory=FortiClientConfig)
    notifications_enabled: bool = Field(default=True)
    notifications: NotificationsConfig = Field(default_factory=NotificationsConfig)

    @field_validator("network_check_url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        if not v.startswith(("http://", "https://")):
            raise ValueError(f"Network check URL must start with http:// or https://: {v}")
        return v

    @field_validator("log_dir")
    @classmethod
    def validate_log_dir(cls, v: str) -> str:
        if not v:
            raise ValueError("Log directory cannot be empty")
        return v

    @model_validator(mode='after')
    def validate_dependencies(self):
        app_names = {app.name for app in self.apps}
        for app in self.apps:
            for dep in app.depends_on:
                if dep not in app_names:
                    raise ValueError(f"App '{app.name}' depends on non-existent app '{dep}'")
        return self

    @model_validator(mode='after')
    def validate_no_circular_dependencies(self):
        def has_cycle(node: str, visited: set, rec_stack: set) -> bool:
            visited.add(node)
            rec_stack.add(node)
            
            app = next((a for a in self.apps if a.name == node), None)
            if app:
                for dep in app.depends_on:
                    if dep not in visited:
                        if has_cycle(dep, visited, rec_stack):
                            return True
                    elif dep in rec_stack:
                        return True
            
            rec_stack.remove(node)
            return False

        for app in self.apps:
            if has_cycle(app.name, set(), set()):
                raise ValueError(f"Circular dependency detected involving app '{app.name}'")
        return self


def load_config(config_path: str = "config.yaml", profile: Optional[str] = None) -> Config:
    """Load and parse configuration from YAML file and environment variables."""
    load_dotenv()
    
    path = Path(config_path)
    
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    
    with open(path, 'r', encoding='utf-8') as f:
        raw = yaml.safe_load(f)
    
    if raw is None:
        raise ValueError(f"Config file is empty: {config_path}")
    
    # Handle profile merging
    if profile:
        profile_path = Path("profiles") / f"{profile}.yaml"
        if profile_path.exists():
            with open(profile_path, 'r', encoding='utf-8') as f:
                profile_raw = yaml.safe_load(f)
            if profile_raw:
                raw = _merge_configs(raw, profile_raw)
    
    # Parse into Pydantic models with validation
    try:
        config = _parse_config(raw)
    except Exception as e:
        raise ValueError(f"Config validation error: {e}")
    
    return config


def _parse_config(raw: dict) -> Config:
    """Parse raw dict into Config model."""
    config_dict = {
        "log_level": "INFO",
        "log_dir": "logs",
        "max_retries": 3,
        "retry_delay": 5,
        "parallel_browsers": False,
        "network_check_url": "https://www.google.com",
        "network_timeout": 10,
        "notifications_enabled": True,
    }
    
    # General settings
    general = raw.get('general', {})
    config_dict["log_level"] = general.get('log_level', 'INFO')
    config_dict["log_dir"] = general.get('log_dir', 'logs')
    config_dict["max_retries"] = general.get('max_retries', 3)
    config_dict["retry_delay"] = general.get('retry_delay', 5)
    config_dict["parallel_browsers"] = general.get('parallel_browsers', False)
    
    # Network
    network = raw.get('network', {})
    config_dict["network_check_url"] = network.get('check_url', 'https://www.google.com')
    config_dict["network_timeout"] = network.get('timeout_seconds', 10)
    
    # VPN
    vpn_raw = raw.get('vpn', {})
    # Priority: Vault > Environment variable > Config file
    vault_password = get_vpn_password()
    password = vault_password or os.environ.get('VPN_PASSWORD') or vpn_raw.get('password')
    config_dict["vpn"] = {
        "enabled": vpn_raw.get('enabled', True),
        "name": vpn_raw.get('name', ''),
        "type": vpn_raw.get('type', 'windows'),
        "wait_after_connect": vpn_raw.get('wait_after_connect', 8),
        "verify_ip_change": vpn_raw.get('verify_ip_change', True),
        "password": password,
        "cisco_path": vpn_raw.get('cisco', {}).get('path'),
        "cisco_host": vpn_raw.get('cisco', {}).get('host'),
    }
    
    # FortiClient
    forti_raw = raw.get('forticlient', {})
    config_dict["forticlient"] = {
        "path": forti_raw.get('path', "C:/Program Files/Fortinet/FortiClient/FortiClient.exe")
    }
    
    # Folders
    config_dict["folders"] = [
        {
            "path": folder.get('path', ''),
            "explorer_view": folder.get('explorer_view', 'details')
        }
        for folder in raw.get('folders', [])
    ]
    
    # IDEs
    config_dict["ides"] = [
        {
            "name": ide.get('name', ''),
            "path": ide.get('path', ''),
            "project": ide.get('project'),
            "wait_seconds": ide.get('wait_seconds', 5)
        }
        for ide in raw.get('ides', [])
    ]
    
    # General Apps
    config_dict["apps"] = [
        {
            "name": app.get('name', ''),
            "path": app.get('path', ''),
            "args": app.get('args', []),
            "wait_seconds": app.get('wait_seconds', 2),
            "depends_on": app.get('depends_on', []),
            "enabled": app.get('enabled', True),
            "conditions": app.get('conditions'),
            "health_check": app.get('health_check', {})
        }
        for app in raw.get('apps', [])
    ]
    
    # Browsers
    browsers = {}
    for name, browser in raw.get('browsers', {}).items():
        urls = [
            {
                "url": url_config.get('url', ''),
                "wait_for": url_config.get('wait_for', 'load')
            }
            for url_config in browser.get('startup_urls', [])
        ]
        
        window_raw = browser.get('window', {})
        browsers[name] = {
            "enabled": browser.get('enabled', True),
            "browser_type": browser.get('browser_type', 'chromium'),
            "profile_dir": browser.get('profile_dir', ''),
            "startup_urls": urls,
            "window": {
                "width": window_raw.get('width', 1920),
                "height": window_raw.get('height', 1080),
                "maximized": window_raw.get('maximized', True)
            }
        }
    config_dict["browsers"] = browsers
    
    # Notifications
    notifications = raw.get('notifications', {})
    config_dict["notifications_enabled"] = notifications.get('enabled', True)
    config_dict["notifications"] = {
        "enabled": notifications.get('enabled', True),
        "on_success": notifications.get('on_success', True),
        "on_failure": notifications.get('on_failure', True),
        "sound": notifications.get('sound', True)
    }
    
    return Config(**config_dict)


def _merge_configs(base: dict, override: dict) -> dict:
    """Merge override config into base config."""
    result = base.copy()
    
    for key, value in override.items():
        if isinstance(value, dict) and key in result and isinstance(result[key], dict):
            result[key] = _merge_configs(result[key], value)
        elif isinstance(value, list) and key in result and isinstance(result[key], list):
            if key in ['apps', 'ides', 'folders']:
                result[key] = value  # Replace lists for apps/ides/folders
            else:
                result[key] = result[key] + value
        else:
            result[key] = value
    
    return result

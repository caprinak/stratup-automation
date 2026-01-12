"""
Unit tests for configuration module
"""
import pytest
from pathlib import Path
import tempfile
import yaml

from core.config import load_config, Config, VPNConfig


class TestConfigLoading:
    """Tests for configuration loading."""
    
    def test_load_valid_config(self, temp_dir):
        """Test loading a valid configuration file."""
        config_content = {
            "general": {
                "log_level": "INFO",
                "max_retries": 3,
            },
            "vpn": {
                "enabled": True,
                "name": "TestVPN",
            },
            "browsers": {},
            "folders": [],
            "ides": [],
        }
        
        config_file = temp_dir / "config.yaml"
        with open(config_file, "w") as f:
            yaml.dump(config_content, f)
        
        config = load_config(str(config_file))
        
        assert config.log_level == "INFO"
        assert config.max_retries == 3
        assert config.vpn.enabled is True
        assert config.vpn.name == "TestVPN"
    
    def test_load_missing_config(self):
        """Test loading a non-existent config file."""
        with pytest.raises(FileNotFoundError):
            load_config("nonexistent.yaml")
    
    def test_default_values(self, temp_dir):
        """Test that default values are applied."""
        config_content = {"general": {}}
        
        config_file = temp_dir / "config.yaml"
        with open(config_file, "w") as f:
            yaml.dump(config_content, f)
        
        config = load_config(str(config_file))
        
        assert config.log_level == "INFO"
        assert config.max_retries == 3
        assert config.vpn.enabled is True


class TestVPNConfig:
    """Tests for VPN configuration."""
    
    def test_vpn_defaults(self):
        """Test VPN configuration defaults."""
        vpn = VPNConfig()
        
        assert vpn.enabled is True
        assert vpn.type == "windows"
        assert vpn.wait_after_connect == 8
    
    def test_vpn_custom_values(self):
        """Test VPN configuration with custom values."""
        vpn = VPNConfig(
            enabled=False,
            name="CustomVPN",
            type="cisco",
            wait_after_connect=15,
        )
        
        assert vpn.enabled is False
        assert vpn.name == "CustomVPN"
        assert vpn.type == "cisco"
        assert vpn.wait_after_connect == 15

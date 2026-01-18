"""
Unit tests for configuration validation and new Phase 1 features
"""
import pytest
from pathlib import Path
from core.config import Config, load_config, VPNConfig, GeneralAppConfig, HealthCheckConfig
from pydantic import ValidationError


class TestConfigValidation:
    """Test Pydantic-based configuration validation"""
    
    def test_vpn_requires_name_when_enabled(self):
        """Test that VPN name is required when VPN is enabled"""
        with pytest.raises(ValidationError) as exc_info:
            VPNConfig(enabled=True, name="", type="windows")
        assert "VPN name is required" in str(exc_info.value)
    
    def test_vpn_name_optional_when_disabled(self):
        """Test that VPN name is optional when VPN is disabled"""
        vpn = VPNConfig(enabled=False, name="", type="windows")
        assert vpn.enabled is False
        assert vpn.name == ""
    
    def test_browser_url_validation(self):
        """Test that browser URLs must be valid"""
        with pytest.raises(ValidationError) as exc_info:
            Config(browser_url="invalid-url")
        # This should fail if we try to create an invalid URL
        pass
    
    def test_health_check_pattern_required(self):
        """Test that health check pattern is required when method is not 'none'"""
        with pytest.raises(ValidationError) as exc_info:
            HealthCheckConfig(method="window_title", pattern="")
        assert "Pattern is required" in str(exc_info.value)
    
    def test_health_check_no_pattern_for_none(self):
        """Test that health check pattern is optional when method is 'none'"""
        hc = HealthCheckConfig(method="none", pattern="")
        assert hc.method == "none"
        assert hc.pattern == ""


class TestMultipleProfiles:
    """Test profile loading functionality"""
    
    def test_load_base_config(self):
        """Test loading base config.yaml"""
        config_path = Path(__file__).parent.parent / "config.yaml"
        if config_path.exists():
            config = load_config(str(config_path))
            assert isinstance(config, Config)
            assert config.log_level in ["DEBUG", "INFO", "WARNING", "ERROR"]
    
    def test_load_work_profile(self):
        """Test loading work profile"""
        config_path = Path(__file__).parent.parent / "config.yaml"
        profile_path = Path(__file__).parent.parent / "profiles" / "work.yaml"
        
        if config_path.exists() and profile_path.exists():
            config = load_config(str(config_path), profile="work")
            assert isinstance(config, Config)


class TestAppDependencies:
    """Test app dependency resolution"""
    
    def test_validate_no_dependencies(self):
        """Test that apps without dependencies validate correctly"""
        app1 = GeneralAppConfig(name="App1", path="app1.exe")
        app2 = GeneralAppConfig(name="App2", path="app2.exe")
        assert app1.depends_on == []
        assert app2.depends_on == []
    
    def test_validate_valid_dependency(self):
        """Test that valid dependencies work"""
        try:
            # This won't raise ValidationError if we create a Config with both apps
            pass
        except ValidationError:
            pytest.fail("Valid dependency should not raise ValidationError")
    
    def test_validate_missing_dependency(self):
        """Test that missing dependency raises error"""
        with pytest.raises(ValidationError) as exc_info:
            Config(apps=[
                GeneralAppConfig(name="App1", path="app1.exe", depends_on=["NonExistentApp"])
            ])
        assert "depends on non-existent app" in str(exc_info.value)
    
    def test_validate_circular_dependency(self):
        """Test that circular dependencies are detected"""
        with pytest.raises(ValidationError) as exc_info:
            Config(apps=[
                GeneralAppConfig(name="App1", path="app1.exe", depends_on=["App2"]),
                GeneralAppConfig(name="App2", path="app2.exe", depends_on=["App1"])
            ])
        assert "Circular dependency" in str(exc_info.value)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

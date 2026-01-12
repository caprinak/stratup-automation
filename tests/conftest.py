"""
Pytest fixtures and configuration
"""
import os
import sys
import pytest
from pathlib import Path
from unittest.mock import MagicMock

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture
def sample_config():
    """Provide sample configuration for tests."""
    return {
        "general": {
            "log_level": "DEBUG",
            "log_dir": "test_logs",
            "max_retries": 2,
        },
        "vpn": {
            "enabled": False,
            "name": "TestVPN",
        },
        "browsers": {
            "test": {
                "enabled": True,
                "browser_type": "chromium",
                "profile_dir": "test_profile",
                "startup_urls": [
                    {"url": "https://example.com", "wait_for": "load"}
                ],
            }
        },
        "folders": [],
        "ides": [],
    }


@pytest.fixture
def temp_dir(tmp_path):
    """Provide temporary directory for tests."""
    return tmp_path


@pytest.fixture
def mock_subprocess(mocker):
    """Mock subprocess for testing system calls."""
    return mocker.patch("subprocess.run", return_value=MagicMock(returncode=0))


@pytest.fixture
def mock_playwright(mocker):
    """Mock Playwright for browser tests."""
    mock_browser = MagicMock()
    mock_context = MagicMock()
    mock_page = MagicMock()
    
    mock_context.pages = [mock_page]
    mock_context.new_page.return_value = mock_page
    mock_browser.new_context.return_value = mock_context
    
    mock_playwright = MagicMock()
    mock_playwright.chromium.launch.return_value = mock_browser
    mock_playwright.chromium.launch_persistent_context.return_value = mock_context
    
    return mocker.patch(
        "playwright.sync_api.sync_playwright",
        return_value=MagicMock(__enter__=MagicMock(return_value=mock_playwright))
    )


# Skip markers for platform-specific tests
def pytest_configure(config):
    config.addinivalue_line(
        "markers", "windows: mark test to run only on Windows"
    )


def pytest_collection_modifyitems(config, items):
    if sys.platform != "win32":
        skip_windows = pytest.mark.skip(reason="Windows-only test")
        for item in items:
            if "windows" in item.keywords:
                item.add_marker(skip_windows)

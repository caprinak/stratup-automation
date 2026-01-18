# Developer Guide

Technical guide for contributing to Startup Automation.

## Table of Contents

1. [Getting Started](#getting-started)
2. [Development Setup](#development-setup)
3. [Code Style](#code-style)
4. [Testing](#testing)
5. [Adding Features](#adding-features)
6. [Debugging](#debugging)
7. [Building](#building)
8. [Release Process](#release-process)

---

## Getting Started

### Prerequisites

- **Python:** 3.10 or later
- **OS:** Windows 10/11 (for VPN/system testing)
- **Git:** For cloning and contributing

### Clone Repository

```bash
git clone https://github.com/caprinak/stratup-automation.git
cd stratup-automation
```

### Development Environment

```bash
# Create virtual environment
python -m venv venv

# Activate (Windows)
.\venv\Scripts\activate

# Install development dependencies
pip install -r requirements-dev.txt

# Install pre-commit hooks (optional)
pre-commit install
```

---

## Development Setup

### Project Structure

```
stratup-automation/
├── main.py                 # Entry point
├── core/                  # Shared utilities
├── phases/                # Execution logic
├── profiles/              # Config profiles
├── tests/                 # Test suite
└── docs/                 # Documentation
```

### Running the Application

```bash
# Run with base config
python main.py

# Run with profile
python main.py --profile work

# Dry run (test config)
python main.py --dry-run

# Run tests
pytest

# Run tests with coverage
pytest --cov=. --cov-report=html
```

---

## Code Style

### Formatting

```bash
# Format all files
black .

# Format imports
isort .

# Both together
black . && isort .
```

### Linting

```bash
# Check for linting errors
ruff check .

# More comprehensive linting
flake8 .

# Type checking
mypy .
```

### Pre-Commit Hooks

Pre-commit hooks automatically run:
- Black formatting
- isort import sorting
- ruff linting
- mypy type checking

### Type Hints

All functions should have type hints:

```python
from typing import Optional, List, Dict

def launch_app(app: GeneralAppConfig) -> bool:
    """Launch a single application."""
    try:
        return True
    except Exception:
        return False
```

### Docstrings

All public functions should have docstrings:

```python
def get_vpn_password() -> Optional[str]:
    """
    Get VPN password from vault.
    
    Returns:
        Password if found, None otherwise
    """
    return VaultManager.get_credential("VPN")
```

---

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run unit tests only
pytest tests/unit

# Run specific test
pytest tests/unit/test_config.py::TestConfigValidation::test_vpn_requires_name

# Run with verbose output
pytest -v

# Run with coverage
pytest --cov=. --cov-report=term-missing
```

### Test Structure

```
tests/
├── unit/             # Unit tests for individual modules
│   ├── test_config.py
│   ├── test_vault.py
│   └── test_conditions.py
├── integration/       # Tests for module interactions
│   ├── test_phases.py
│   └── test_metrics.py
└── e2e/            # End-to-end tests
    └── test_full_startup.py
```

### Writing Tests

```python
import pytest
from core.config import Config

class TestConfigValidation:
    """Test configuration validation."""
    
    def test_vpn_requires_name_when_enabled(self):
        """Test that VPN name is required when VPN is enabled."""
        with pytest.raises(ValidationError) as exc_info:
            VPNConfig(enabled=True, name="", type="windows")
        assert "VPN name is required" in str(exc_info.value)
    
    def test_vpn_name_optional_when_disabled(self):
        """Test that VPN name is optional when VPN is disabled."""
        vpn = VPNConfig(enabled=False, name="", type="windows")
        assert vpn.enabled is False
```

### Test Fixtures

Create reusable fixtures in `tests/conftest.py`:

```python
import pytest
from core.config import load_config

@pytest.fixture
def config():
    """Provide a valid config object."""
    return load_config("tests/fixtures/valid_config.yaml")

@pytest.fixture
def mock_vpn_password(monkeypatch):
    """Mock VPN password."""
    monkeypatch.setattr("core.vault.get_vpn_password", lambda: "test123")
    yield
```

---

## Adding Features

### Adding a New Phase

**1. Create Phase Module:**

```python
# phases/phase4_custom.py
from core.config import Config
from core.logger import get_logger

class CustomPhase:
    """Handle custom phase tasks."""
    
    def __init__(self, config: Config):
        self.config = config
        self.logger = get_logger()
    
    def run(self) -> bool:
        """Execute all custom phase tasks."""
        self.logger.info("=" * 50)
        self.logger.info("PHASE 4: Custom")
        self.logger.info("=" * 50)
        
        try:
            # Your logic here
            self.logger.info("Custom phase completed")
            return True
        except Exception as e:
            self.logger.error(f"Custom phase failed: {e}")
            raise
```

**2. Integrate in main.py:**

```python
# Import phase
from phases.phase4_custom import CustomPhase

# In main() function
phase4 = CustomPhase(config)
results["phase4"] = phase4.run()
```

**3. Add Config Support (if needed):**

```python
# In core/config.py

@dataclass
class CustomConfig:
    enabled: bool = True
    setting: str = ""

class Config(BaseModel):
    # ... existing fields ...
    custom: CustomConfig = Field(default_factory=CustomConfig)
```

### Adding VPN Support

**1. Add VPN Type to Config:**

```python
# In core/config.py
class VPNConfig(BaseModel):
    type: Literal["windows", "cisco", "nordvpn", "forticlient", "myvpn"]
    # ... other fields ...
```

**2. Implement Connection Logic:**

```python
# In phases/phase1_system.py

def _connect_vpn(self):
    """Connect to VPN based on type."""
    if self.config.vpn.type == "myvpn":
        self._connect_myvpn_vpn()
    # ... other types

def _connect_myvpn_vpn(self):
    """Connect to MyVPN using CLI."""
    import subprocess
    result = subprocess.run(
        ["myvpn", "connect", self.config.vpn.name],
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        raise ConnectionError(f"MyVPN failed: {result.stderr}")
```

**3. Add Tests:**

```python
# In tests/unit/test_vpn.py

def test_myvpn_connection(monkeypatch):
    """Test MyVPN connection logic."""
    mock_subprocess = MagicMock()
    monkeypatch.setattr("subprocess.run", mock_subprocess)
    # ... test implementation
```

### Adding Health Check Methods

**1. Add Method to Config:**

```python
# In core/config.py

class HealthCheckConfig(BaseModel):
    method: Literal["window_title", "port", "process", "http", "none"]
```

**2. Implement Check Logic:**

```python
# In phases/phase2_apps.py

def _perform_health_check(self, app: GeneralAppConfig) -> bool:
    """Perform health check for an application."""
    method = app.health_check.method
    
    if method == "http":
        return self._check_http_endpoint(app.health_check.pattern)
    # ... existing methods

def _check_http_endpoint(self, url: str) -> bool:
    """Check if HTTP endpoint is responding."""
    try:
        import requests
        response = requests.get(url, timeout=5)
        return response.status_code == 200
    except Exception:
        return False
```

---

## Debugging

### Logging

**View Real-Time Logs:**

```bash
# Tail logs
Get-Content logs\startup_YYYY-MM-DD.log -Wait

# View in separate terminal
.\venv\Scripts\python main.py 2>&1 | Tee-Object -FilePath logs\debug.txt
```

**Log Levels:**

```python
# Set in config.yaml
general:
  log_level: "DEBUG"  # Most verbose

# Or set via environment
set LOG_LEVEL=DEBUG && python main.py
```

### Debugger

```bash
# Use Python debugger
python -m pdb main.py --dry-run

# Or in VS Code with launch.json:
{
    "version": "0.2.0",
    "configurations": [{
        "name": "Python: Current File",
        "type": "python",
        "request": "launch",
        "program": "${file}",
        "console": "integratedTerminal",
        "justMyCode": false
    }]
}
```

### Common Issues

**Import Error:**
```bash
# Module not found? Install it
pip install pydantic
```

**Config Validation Error:**
```bash
# Use dry-run to see validation errors
python main.py --dry-run
```

**Playwright Not Installed:**
```bash
# Install Playwright browsers
playwright install chromium
```

---

## Building

### Build Wheel

```bash
python -m build
# Output: dist/stratup-automation-X.X.X-py3-none-any.whl
```

### Build Executable

```bash
# Build standalone EXE
pyinstaller launcher.py --onefile --windowed --name="StartupLauncher"

# Output: dist/StartupLauncher.exe
```

### Clean Build

```bash
# Remove build artifacts
rm -rf build/ dist/ *.egg-info
```

---

## Release Process

### Version Bump

1. Update `__version__` in `__init__.py`
2. Update version in `pyproject.toml`
3. Update CHANGELOG.md

### Tag Release

```bash
git tag -a v1.2.0 -m "Release v1.2.0"
git push origin v1.2.0
```

### Create GitHub Release

```bash
# CI/CD will automatically create release
# Or manually via GitHub UI
```

---

## Contributing Guidelines

### Pull Request Process

1. **Fork** the repository
2. **Create** feature branch (`git checkout -b feature/my-feature`)
3. **Make** changes with tests
4. **Run** tests and linting
5. **Commit** with clear message
6. **Push** to your fork
7. **Create** Pull Request

### Commit Messages

Format: `<type>(<scope>): <description>`

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `refactor`: Code refactoring
- `test`: Test changes
- `chore`: Maintenance

**Examples:**
```
feat(vpn): add support for OpenVPN
fix(apps): resolve dependency cycle for database apps
docs(config): add profile examples
```

### Code Review Checklist

- [ ] Code follows style guidelines (black, ruff)
- [ ] Tests added/updated
- [ ] All tests passing
- [ ] Documentation updated
- [ ] No breaking changes (or documented)
- [ ] Type hints added
- [ ] Docstrings added

---

## Performance

### Profiling

```bash
# Profile execution time
python -m cProfile -o profile.stats main.py --dry-run

# View profile
python -m pstats profile.stats
```

### Optimization Tips

1. **Use parallel_browsers** for faster startup
2. **Reduce wait_seconds** where safe
3. **Optimize wait_for** strategies (use `load` for simple pages)
4. **Disable unused apps** and browsers
5. **Use conditions** to skip unnecessary launches

---

## Security

### Password Handling

**Do NOT:**
- Log passwords
- Print passwords
- Store in config files
- Commit to git

**DO:**
- Use `--set-password` for secure storage
- Use Windows Credential Manager
- Check `.env` is in `.gitignore`

### Input Validation

Always validate user input:

```python
def set_vpn_password(password: str) -> bool:
    """Set VPN password in vault."""
    if not password or len(password) < 8:
        raise ValueError("Password must be at least 8 characters")
    # ... rest of implementation
```

---

## CI/CD

### GitHub Actions

The project uses GitHub Actions for CI/CD.

**Workflows:**
- `.github/workflows/ci.yml` - On every push/PR
- `.github/workflows/release.yml` - On version tags

**CI Checks:**
- Linting (black, ruff, mypy)
- Security (bandit, pip-audit)
- Tests (unit, integration, e2e)
- Build verification

### Local Testing Before Push

```bash
# Run same checks as CI
black . && isort .
ruff check .
mypy .
pytest
```

---

## Resources

### Documentation

- [Pydantic Documentation](https://docs.pydantic.dev/)
- [Playwright Documentation](https://playwright.dev/python/)
- [pytest Documentation](https://docs.pytest.org/)
- [pystray Documentation](https://pystray.readthedocs.io/)

### Tools

- [Black](https://black.readthedocs.io/) - Code formatter
- [Ruff](https://docs.astral.sh/ruff/) - Linter
- [MyPy](https://mypy.readthedocs.io/) - Type checker
- [Pre-Commit](https://pre-commit.com/) - Git hooks

### Community

- [GitHub Issues](https://github.com/caprinak/stratup-automation/issues)
- [GitHub Discussions](https://github.com/caprinak/stratup-automation/discussions)
- [PyPI](https://pypi.org/project/stratup-automation/)

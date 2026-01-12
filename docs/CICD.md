# CI/CD Pipeline Documentation

The Startup Automation project uses **GitHub Actions** for Continuous Integration and Continuous Deployment (CI/CD). This document details the pipeline architecture, workflows, and configuration.

## 🚀 Overview

The pipeline is designed to ensure code quality across platforms (Windows & Linux) and automate releases.

| Workflow | Trigger | Description |
|----------|---------|-------------|
| **CI Pipeline** | Push/PR to `main`, `develop` | Runs linting, security checks, unit tests (Ubuntu/Windows), and build verification. |
| **Release** | Tag push `v*.*.*` | Builds the application, generates an executable (EXE), and creates a GitHub Release. |
| **Dependabot** | Weekly (Monday) | Checks for dependency updates for pip and GitHub Actions. |

## 🛠️ Workflows

### 1. CI Pipeline (`ci.yml`)

This is the primary workflow that runs on every core code change.

**Jobs:**
*   **Lint & Format**: Checks code style using `black`, `isort`, `ruff`, and `flake8`. Enforces type hints with `mypy`.
*   **Security Scan**:
    *   `bandit`: Checks for common security issues in Python code.
    *   `pip-audit`: Checks dependencies for known vulnerabilities.
*   **Test (Ubuntu)**: Runs unit tests on Linux to ensure cross-platform compatibility and generates coverage reports.
*   **Test (Windows)**:
    *   Runs unit tests on Windows (Python 3.10, 3.11, 3.12).
    *   Runs **Integration Tests** to verify VPN and Windows system interactions.
    *   Runs **Playwright E2E Tests**.
*   **Build Check**: Verifies the project can be built into a package and an executable (`.exe`).

### 2. Release Automation (`release.yml`)

Triggered automatically when a semantic version tag (e.g., `v1.0.0`) is pushed.

**Steps:**
1.  **Build**: Creates a distribution package (`wheel` / `sdist`).
2.  **Freeze**: Uses `PyInstaller` to create a standalone `startup-automation.exe`.
    *   Bundles `config.yaml` and `templates/` into the executable.
3.  **Changelog**: Auto-generates a list of changes from commit messages.
4.  **Publish**: Creates a GitHub Release with the artifacts and changelog.

### 3. Dependency Management (`dependabot.yml`)

*   **Schedule**: Weekly updates.
*   **Scope**:
    *   `pip` packages (Python dependencies).
    *   `github-actions` (workflow versions).

## ⚙️ Configuration Files

*   **`.github/workflows/`**: Contains the YAML workflow definitions.
*   **`pyproject.toml`**: Centralized configuration for tools (`pytest`, `black`, `ruff`, `mypy`).
*   **`requirements-dev.txt`**: Dependencies required for testing and linting (not for production use).

## 🧪 Local Testing

Before pushing, you can run the same checks locally:

### 1. Install Dev Dependencies
```bash
pip install -r requirements-dev.txt
```

### 2. Run Formatters & Linters
```bash
black .
isort .
ruff check .
mypy .
```

### 3. Run Tests
```bash
# Run unit tests
pytest tests/unit

# Run all tests (requires VPN/Network access for integration)
pytest
```

## 🔐 Secrets

The following GitHub Secrets may be required for specific integrations (if enabled):

*   `CODECOV_TOKEN`: For uploading coverage reports to Codecov (optional).
*   `PYPI_TOKEN`: For publishing to PyPI (optional, for future use).

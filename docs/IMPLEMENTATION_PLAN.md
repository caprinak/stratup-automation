# Implementation Plan: Project Enhancements

## Overview

This document outlines the planned enhancements for the Startup Automation project. Features are prioritized by impact and complexity.

---

## Phase 1: Quick Wins (Low Complexity, High Impact)

### 1.1 Config Validation
**Priority**: High | **Complexity**: Low | **Est. Time**: 2-3 hours

**Problem**: Configuration errors only surface at runtime, often with cryptic error messages.

**Implementation**:
- Add `pyyaml` schema validation using `pydantic` or `strictyaml`
- Validate paths exist before launching apps
- Validate URLs are well-formed
- Provide clear error messages with line numbers

**Files to Modify**:
- `requirements.txt` - Add `pydantic` or `strictyaml`
- `core/config.py` - Add validation logic
- `tests/unit/test_config.py` - Add validation tests

**Success Criteria**:
- Invalid config throws clear error on startup
- All existing valid configs continue to work

---

### 1.2 Multiple Profiles Support
**Priority**: High | **Complexity**: Low | **Est. Time**: 2 hours

**Problem**: Users need to manually edit config.yaml to switch between work/home setups.

**Implementation**:
- Add `profiles/` directory with `work.yaml`, `home.yaml`, `travel.yaml`
- Add `--profile` CLI flag: `python main.py --profile work`
- Add profile selector in system tray menu
- Profile inherits base config from `config.yaml`

**Files to Modify**:
- `core/config.py` - Add profile loading logic
- `main.py` - Add `--profile` argument
- `launcher.py` - Add profile selector menu item

**Success Criteria**:
- Can switch profiles via CLI
- Can switch profiles via system tray
- Profiles merge correctly with base config

---

### 1.3 App Dependencies
**Priority**: Medium | **Complexity**: Low | **Est. Time**: 1 hour

**Problem**: Apps launch simultaneously even when one depends on another (e.g., IDE before opening project).

**Implementation**:
- Add `depends_on: [app_name]` field to app config
- Topological sort to determine launch order
- Visual dependency graph in logs

**Files to Modify**:
- `core/config.py` - Add `depends_on` field
- `phases/phase2_apps.py` - Add dependency resolution

**Success Criteria**:
- Apps launch in correct order
- Circular dependencies are detected and reported

---

### 1.4 Health Checks
**Priority**: Medium | **Complexity**: Low | **Est. Time**: 2 hours

**Problem**: Apps may fail silently, leaving the user unaware.

**Implementation**:
- Add `health_check: {method: "window_title|port|process", pattern: "..."}` to app config
- Verify app launched successfully after wait_seconds
- Retry failed launches up to max_retries
- Report failed health checks in summary

**Files to Modify**:
- `core/config.py` - Add health check config
- `phases/phase2_apps.py` - Add health check logic

**Success Criteria**:
- Failed app launches are detected and retried
- Final summary shows all failures

---

## Phase 2: Medium Complexity Features

### 2.1 Conditional Startup
**Priority**: Medium | **Complexity**: Medium | **Est. Time**: 4 hours

**Problem**: Different apps needed based on time of day, day of week, or network location.

**Implementation**:
- Add `conditions: {time_range: "9:00-17:00", days: ["Mon-Fri"], networks: ["WorkVPN"]}` to app config
- Evaluate conditions before launching each app
- Add network-based detection (IP ranges, SSID)

**Files to Modify**:
- `core/config.py` - Add conditions dataclass
- `phases/` - Add condition evaluator
- `main.py` - Skip apps that don't match conditions

**Success Criteria**:
- Apps launch only when conditions match
- Dry-run shows which apps will launch

---

### 2.2 Startup Metrics & History
**Priority**: Medium | **Complexity**: Medium | **Est. Time**: 4 hours

**Problem**: No visibility into startup performance trends over time.

**Implementation**:
- Store metrics in `logs/metrics.jsonl` (newline-delimited JSON)
- Track: total duration, phase times, failures, retry counts
- Add `--metrics` CLI flag to show history
- Add "View Metrics" to system tray menu
- Generate simple ASCII charts

**Files to Modify**:
- `core/metrics.py` - New file for metrics tracking
- `main.py` - Record metrics on completion
- `launcher.py` - Add metrics viewer

**Success Criteria**:
- Metrics recorded for each run
- Can view historical trends
- Charts show performance over time

---

### 2.3 Parallel Browser Execution
**Priority**: Medium | **Complexity**: Medium | **Est. Time**: 3 hours

**Problem**: `parallel_browsers` flag exists but is not implemented.

**Implementation**:
- Use `concurrent.futures.ThreadPoolExecutor` for browser phase
- Ensure proper resource cleanup
- Add per-browser timeout to prevent hangs

**Files to Modify**:
- `phases/phase3_browsers.py` - Implement parallel launch

**Success Criteria**:
- Multiple browsers launch simultaneously when enabled
- All browsers complete successfully
- Fallback to sequential on error

---

### 2.4 Windows Credential Manager Integration
**Priority**: High | **Complexity**: Medium | **Est. Time**: 3 hours

**Problem**: VPN passwords stored in .env are insecure and visible in plain text.

**Implementation**:
- Use `pywin32` to access Windows Credential Manager
- Add `--set-password` CLI flag to store credentials
- Load passwords from Credential Manager at runtime
- Fall back to .env if credentials not found

**Files to Modify**:
- `requirements.txt` - Add `pywin32`
- `core/vault.py` - New file for credential manager wrapper
- `phases/phase1_system.py` - Load password from vault

**Success Criteria**:
- Can store VPN password securely
- Passwords loaded automatically at runtime
- No passwords in plain text files

---

## Phase 3: Advanced Features

### 3.1 Config Editor Dashboard (Web UI)
**Priority**: Medium | **Complexity**: High | **Est. Time**: 8-12 hours

**Problem**: Editing YAML manually is error-prone for non-technical users.

**Implementation**:
- Build Flask/FastAPI web app in `dashboard/` directory
- Features:
  - Visual config editor (forms, checkboxes, dropdowns)
  - Real-time YAML preview
  - Test config button (dry-run)
  - Profile manager
  - Metrics viewer
- Auto-reload on config changes
- Start via `python dashboard/app.py`

**Files to Modify**:
- `requirements.txt` - Add web framework
- `dashboard/app.py` - New Flask/FastAPI app
- `dashboard/templates/` - HTML templates
- `dashboard/static/` - CSS/JS

**Success Criteria**:
- Can edit all config fields via web UI
- Real-time validation
- Can test changes without restarting launcher

---

### 3.2 Auto-Update Mechanism
**Priority**: Low | **Complexity**: High | **Est. Time**: 6-8 hours

**Problem**: Manual updates via git pull are inconvenient for non-developers.

**Implementation**:
- Check GitHub releases on startup (optional `--check-updates`)
- Download new version to temp directory
- Self-updater script that runs on next launcher restart
- Preserve user config during update
- Rollback on failure

**Files to Modify**:
- `core/updater.py` - New file
- `launcher.py` - Add update checker
- `update.py` - Standalone updater script

**Success Criteria**:
- Automatically detects new releases
- Updates without user intervention
- Preserves user configurations

---

### 3.3 Location-Based Automation
**Priority**: Low | **Complexity**: High | **Est. Time**: 6 hours

**Problem**: Users want different automation setups when traveling vs at home/office.

**Implementation**:
- Detect location via Wi-Fi SSID or IP geolocation
- Auto-switch profiles based on location
- Add manual location override in system tray
- Cache location to avoid repeated checks

**Files to Modify**:
- `core/location.py` - New file
- `core/config.py` - Add location mapping
- `launcher.py` - Auto-detect and switch profiles

**Success Criteria**:
- Profile auto-switches based on location
- Can manually override location
- Works offline with cached location

---

## Phase 4: Quality & Testing Improvements

### 4.1 Expanded Test Suite
**Priority**: Medium | **Complexity**: Medium | **Est. Time**: 8 hours

**Problem**: Limited test coverage, especially for VPN and browser automation.

**Implementation**:
- Add unit tests for all config validators
- Add integration tests for each phase (using mocks)
- Add E2E tests with sample config
- Test VPN connection with mock subprocess
- Test browser automation with mock Playwright
- Target 80% code coverage

**Files to Modify**:
- `tests/unit/` - Expand tests
- `tests/integration/` - Add phase tests
- `tests/fixtures/` - Add sample configs
- `pytest.ini` - Configure coverage

**Success Criteria**:
- 80%+ code coverage
- All phases tested with mocks
- CI runs tests on every commit

---

### 4.2 Pre-Commit Hooks & Linting
**Priority**: Medium | **Complexity**: Low | **Est. Time**: 2 hours

**Problem**: Code style inconsistencies and syntax errors slip into commits.

**Implementation**:
- Set up `pre-commit` framework
- Add hooks: `black`, `ruff`, `mypy`, `isort`
- Add config file validation hook
- Add YAML linting with `yamllint`

**Files to Modify**:
- `requirements-dev.txt` - Add dev tools
- `.pre-commit-config.yaml` - New file
- `pyproject.toml` - Add tool configs

**Success Criteria**:
- Code auto-formatted on commit
- Type checking before commit
- Config validated before commit

---

### 4.3 Documentation Improvements
**Priority**: Low | **Complexity**: Low | **Est. Time**: 4 hours

**Implementation**:
- Add inline docstrings to all functions
- Add type hints everywhere
- Create architecture decision records (ADRs)
- Add video tutorials for common tasks
- Add troubleshooting section to USER_MANUAL.md

**Files to Modify**:
- All Python files - Add docstrings
- `docs/ADRs/` - New directory
- `README.md` - Add quickstart video

**Success Criteria**:
- 100% function docstring coverage
- Clear troubleshooting guide
- Video walkthrough available

---

## Implementation Priority Summary

| Phase | Features | Est. Total Time |
|-------|----------|-----------------|
| **Phase 1** (Quick Wins) | Config Validation, Multiple Profiles, App Dependencies, Health Checks | ~7 hours |
| **Phase 2** (Medium) | Conditional Startup, Metrics, Parallel Browsers, Credential Manager | ~14 hours |
| **Phase 3** (Advanced) | Dashboard, Auto-Update, Location-Based | ~26 hours |
| **Phase 4** (Quality) | Testing, Pre-Commit, Docs | ~14 hours |

**Grand Total**: ~61 hours of development

---

## Recommended Implementation Order

1. **Start with Phase 1** - These provide immediate value with low risk
2. **Implement Credential Manager** (2.4) - High security priority
3. **Add Conditional Startup** (2.1) - Useful for power users
4. **Build Metrics** (2.2) - Provides visibility for further improvements
5. **Implement Parallel Browsers** (2.3) - Performance improvement
6. **Expand Testing** (4.1) - Foundation for stable features
7. **Add Pre-Commit Hooks** (4.2) - Prevent regressions
8. **Build Dashboard** (3.1) - Major UX improvement
9. **Auto-Update** (3.2) - Convenience feature
10. **Location-Based** (3.3) - Nice-to-have

---

## Notes

- All features should be backward compatible with existing configs
- New CLI flags should have sensible defaults
- System tray should remain simple and responsive
- Performance impact should be minimal (especially on startup)
- Security first: passwords should never be logged or displayed

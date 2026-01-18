# Architecture

System design and architecture for Startup Automation.

## Overview

Startup Automation follows a **Phased Execution Model** orchestrated by `main.py`, with three main phases that run in sequence.

```
┌─────────────────────────────────────────────────────────────┐
│                    main.py                            │
│  ┌────────────────────────────────────────────────────┐  │
│  │ Load Config (Pydantic validation)        │  │
│  │  └─> config.yaml + profiles/            │  │
│  └────────────────────────────────────────────────────┘  │
│                                                      │
│  ┌────────────────────────────────────────────────────┐  │
│  │ Phase 2: Applications                        │  │
│  │  ├─> Open Folders (Explorer)                │  │
│  │  ├─> Launch IDEs                             │  │
│  │  └─> Launch Apps (with dependencies)        │  │
│  └────────────────────────────────────────────────────┘  │
│                                                      │
│  ┌────────────────────────────────────────────────────┐  │
│  │ Phase 3: Browsers                           │  │
│  │  └─> Playwright persistent contexts          │  │
│  └────────────────────────────────────────────────────┘  │
│                                                      │
│  ┌────────────────────────────────────────────────────┐  │
│  │ Phase 1: System (VPN)                        │  │
│  │  ├─> Network Check                         │  │
│  │  └─> VPN Connection (last)                │  │
│  └────────────────────────────────────────────────────┘  │
│                                                      │
│  ┌────────────────────────────────────────────────────┐  │
│  │ Metrics & Logging                             │  │
│  │  ├─> logs/ (daily files)                  │  │
│  │  ├─> metrics.jsonl (history)              │  │
│  │  └─> Toast Notifications                    │  │
│  └────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## Directory Structure

```
stratup-automation/
├── main.py                 # Entry point, orchestrates all phases
├── launcher.py             # System tray launcher with pystray
├── start_launcher.vbs       # Silent startup script
├── setup.ps1              # Installation script
├── create_scheduled_task.ps1  # Windows task scheduler script
├── config.yaml             # Base configuration
├── .env                   # Environment variables (VPN password)
├── requirements.txt        # Production dependencies
├── requirements-dev.txt    # Development dependencies
├── pyproject.toml         # Tool configurations
│
├── core/                  # Shared utilities
│   ├── config.py           # Pydantic models & validation
│   ├── vault.py           # Windows Credential Manager
│   ├── conditions.py       # Condition evaluator
│   ├── metrics.py         # Metrics tracking
│   ├── logger.py          # Logging setup
│   ├── retry.py           # Retry decorator
│   └── notifier.py        # Toast notifications
│
├── phases/                # Execution logic
│   ├── phase1_system.py   # Network + VPN
│   ├── phase2_apps.py     # Folders + IDEs + Apps
│   └── phase3_browsers.py # Browsers (Playwright)
│
├── profiles/              # Profile configurations
│   ├── work.yaml         # Work profile
│   └── home.yaml         # Home profile
│
├── logs/                 # Runtime logs
│   ├── startup_YYYY-MM-DD.log
│   └── metrics.jsonl
│
├── browser_data/          # Persistent browser data
│   ├── work_profile/
│   └── personal_profile/
│
├── tests/                 # Test suite
│   ├── unit/             # Unit tests
│   ├── integration/       # Integration tests
│   └── e2e/             # End-to-end tests
│
└── docs/                 # Documentation
    ├── USER_GUIDE.md
    ├── CONFIGURATION.md
    ├── ARCHITECTURE.md
    └── DEVELOPER_GUIDE.md
```

---

## Core Components

### Configuration System (`core/config.py`)

**Technology:** Pydantic v2

**Responsibilities:**
- Load and validate YAML configuration
- Support profile merging
- Type-safe configuration access
- Validate constraints and relationships

**Data Flow:**
```
config.yaml
    ↓
profiles/{name}.yaml (optional)
    ↓
Pydantic Models (validation)
    ↓
Config object (type-safe)
```

**Validation Features:**
- Field-level constraints (ranges, allowed values)
- Cross-field validation (dependencies, circular refs)
- URL validation
- Type checking (int, str, bool, etc.)

### Condition Evaluator (`core/conditions.py`)

**Responsibilities:**
- Evaluate time-based conditions
- Evaluate day-based conditions
- Evaluate network-based conditions
- WiFi SSID detection
- IP subnet detection

**Supported Conditions:**
```python
{
    "time_range": "9:00-17:00",  # HH:MM-HH:MM format
    "days": "weekdays",          # weekdays, weekends, Mon-Fri, Mon,Wed,Fri
    "networks": "OfficeWiFi"      # WiFi SSID or IP subnet
}
```

### Vault (`core/vault.py`)

**Technology:** pywin32 (Windows Credential Manager)

**Responsibilities:**
- Secure password storage
- Credential CRUD operations
- Fallback to environment variables

**Priority Order:**
1. Windows Credential Manager (most secure)
2. Environment Variable (`VPN_PASSWORD`)
3. Config file (least secure, not recommended)

### Metrics Tracker (`core/metrics.py`)

**Responsibilities:**
- Track execution time per phase
- Record success/failure status
- Store retry counts
- Generate ASCII charts

**Storage:** Newline-delimited JSON (`logs/metrics.jsonl`)

**Metrics Structure:**
```json
{
    "timestamp": "2024-01-18T12:00:00",
    "profile": "work",
    "duration_seconds": 45.2,
    "phases": {
        "phase1": {"duration": 10.5, "success": true},
        "phase2": {"duration": 30.2, "success": true},
        "phase3": {"duration": 4.5, "success": true}
    },
    "errors": [],
    "retries": {},
    "overall_success": true
}
```

---

## Phases

### Phase 1: System (`phases/phase1_system.py`)

**Execution Order:** Last (after apps and browsers)

**Responsibilities:**
1. Network connectivity check
2. VPN connection (if enabled)
3. IP change verification

**Network Check:**
```python
# HTTP request to configured URL
urllib.request.urlopen(config.network_check_url, timeout=10)
```

**VPN Connection:**
- Type: Windows, Cisco, NordVPN, FortiClient
- Retry logic: Exponential backoff
- IP verification: Before/after comparison

### Phase 2: Applications (`phases/phase2_apps.py`)

**Execution Order:** First (before VPN and browsers)

**Responsibilities:**
1. Open folders in Explorer
2. Launch IDEs
3. Launch general apps

**Dependency Resolution:**
- Algorithm: Topological sort (Kahn's algorithm)
- Purpose: Ensure apps start in correct order
- Validation: Detect circular dependencies

**Health Checks:**
- Method: window_title, port, or process
- Retry: Configurable attempts
- Timeout: Per-app timeout

### Phase 3: Browsers (`phases/phase3_browsers.py`)

**Execution Order:** Middle (after apps, before VPN)

**Technology:** Playwright

**Responsibilities:**
1. Launch browser with persistent context
2. Open multiple tabs
3. Wait for page load strategies

**Persistence Mechanism:**
```python
# Launch with persistent context
browser_type.launch_persistent_context(
    user_data_dir=profile_dir,
    headless=False,
    # ... other options
)
# Browser stays open after Python script exits
```

**Execution Modes:**
- **Sequential:** One browser at a time (default)
- **Parallel:** Multiple browsers simultaneously (`parallel_browsers: true`)

---

## System Tray (`launcher.py`)

**Technology:** pystray

**Features:**
- Background process (daemon)
- Threaded execution (non-blocking UI)
- Silent startup (no console window)
- Right-click context menu

**Menu Structure:**
```
🚀 Run Startup Now
👤 Profiles
  ├─> Work
  └─> Home
⚙️ Settings (Open Config)
📁 Open Logs
📊 View Metrics
❌ Exit Launcher
```

---

## Data Flow

### Startup Sequence

```
User Action (Launch)
    ↓
launcher.py (System Tray)
    ↓
main.py --profile work
    ↓
load_config()
    ├─> config.yaml
    └─> profiles/work.yaml (merge)
    ↓
Phase 2: Apps
    ├─> Check conditions (time, day, network)
    ├─> Resolve dependencies (topological sort)
    ├─> Launch apps with health checks
    └─> Record phase time
    ↓
Phase 3: Browsers
    ├─> Launch Playwright contexts
    ├─> Open URLs with wait strategies
    └─> Record phase time
    ↓
Phase 1: VPN
    ├─> Check network connectivity
    ├─> Get VPN password (vault/env)
    ├─> Connect VPN
    └─> Record phase time
    ↓
metrics.save()
    ↓
logs/metrics.jsonl
```

### Configuration Loading

```
config.yaml (base)
    ↓
profiles/work.yaml (override)
    ↓
Merge Strategy:
    - Primitive values: Replace
    - Lists (apps, folders): Replace
    - Dicts (deep merge): Merge
    ↓
Pydantic Validation
    ↓
Type-safe Config object
```

---

## Concurrency Model

### Parallel Browser Execution

```python
if config.parallel_browsers:
    with ThreadPoolExecutor(max_workers=len(browsers)) as executor:
        futures = {
            executor.submit(launch_browser, name, cfg)
            for name, cfg in browsers.items()
        }
        for future in as_completed(futures):
            future.result()
```

### App Dependencies (Sequential)

```python
# Always sequential for apps
launch_order = topological_sort(apps)
for app_name in launch_order:
    launch_app(app_name)
    # Waits for health check + wait_seconds
```

### Threading in Launcher

```python
# Main thread: System tray UI (pystray)
# Worker thread: Startup execution (daemon)
def on_launch():
    thread = Thread(target=run_automation, daemon=True)
    thread.start()
```

---

## Security Model

### Password Storage

**Priority (most to least secure):**
1. **Windows Credential Manager** (encrypted by Windows)
2. **Environment Variable** (process memory only)
3. **Config File** (plain text - NOT recommended)

**Implementation:**
```python
# core/vault.py
win32cred.CredWrite({
    "Type": 1,  # CRED_TYPE_GENERIC
    "TargetName": "StratupAutomation_VPN",
    "CredentialBlob": password,
    "Persist": 2,  # CRED_PERSIST_LOCAL_MACHINE
}, 0)
```

### Logging

**What is NOT logged:**
- VPN passwords
- API keys
- Authentication credentials

**What IS logged:**
- App launch success/failure
- Phase durations
- Error messages (sanitized)
- Network status
- Dependency resolution order

---

## Error Handling

### Retry Strategy

```python
@retry(max_attempts=3, delay=5)
def vpn_connect():
    # Attempts up to 3 times
    # Waits 5 seconds between attempts
    # Exponential backoff could be added
    pass
```

### Validation Errors

```python
# Pydantic ValidationError
try:
    config = Config(**data)
except ValidationError as e:
    # Clear error message with field path
    # Example: "vpn.name: Cannot be empty"
    sys.exit(1)
```

### Runtime Errors

- **App Launch Failed:** Logged, app skipped, continue with next
- **VPN Failed:** Logged, continue with remaining phases
- **Health Check Failed:** Retry up to max, then skip app
- **Network Timeout:** Retry, then proceed without VPN

---

## Extension Points

### Adding a New Phase

```python
# 1. Create phase file
# phases/phase4_custom.py

class CustomPhase:
    def __init__(self, config: Config):
        self.config = config
        self.logger = get_logger()

    def run(self) -> bool:
        try:
            # Your logic here
            self.logger.info("Custom phase complete")
            return True
        except Exception as e:
            self.logger.error(f"Custom phase failed: {e}")
            return False

# 2. Add to main.py
from phases.phase4_custom import CustomPhase

# In main() after other phases:
phase4 = CustomPhase(config)
results["phase4"] = phase4.run()
```

### Adding a New VPN Type

```python
# In phases/phase1_system.py

def _connect_vpn(self):
    if self.config.vpn.type == "myvpn":
        self._connect_myvpn_vpn()
    elif self.config.vpn.type == "custom":
        self._connect_custom_vpn()

def _connect_myvpn_vpn(self):
    subprocess.run(["myvpn", "connect"], ...)
```

### Adding a New Health Check Method

```python
# In phases/phase2_apps.py

def _check_health(self, app: GeneralAppConfig) -> bool:
    if app.health_check.method == "http":
        return self._check_http_endpoint(app.health_check.pattern)
    # ... existing methods
```

---

## Performance Considerations

### Startup Time

**Factors:**
- Number of apps/browsers
- Wait times per app
- Network connectivity
- VPN connection time

**Optimization:**
- Enable parallel browsers for faster startup
- Reduce wait_seconds where possible
- Use appropriate wait_for strategies
- Disable unnecessary apps/browsers

### Memory Usage

**Contributors:**
- Playwright browser instances
- Pystray system tray
- Logging buffers

**Mitigation:**
- Browser processes are detached (don't share Python memory)
- Logs are rotated (daily files)
- Minimal Python objects kept in memory

### Disk Usage

**Locations:**
- `logs/` - Daily rotation (old logs should be cleaned)
- `browser_data/` - Grows over time (clear if needed)
- `metrics.jsonl` - Append-only, grows indefinitely

**Recommendations:**
- Clean logs older than 30 days
- Clear browser profiles if issues arise
- Archive metrics.jsonl periodically

---

## Testing Strategy

### Unit Tests

**Location:** `tests/unit/`

**Scope:**
- Config validation
- Condition evaluation
- Dependency resolution
- Metrics formatting
- Vault operations

### Integration Tests

**Location:** `tests/integration/`

**Scope:**
- VPN connection (mocked subprocess)
- App launching (mocked Popen)
- Browser phase (mocked Playwright)

### E2E Tests

**Location:** `tests/e2e/`

**Scope:**
- Full startup sequence
- Profile switching
- System tray interaction
- Metrics recording

---

## Deployment

### Windows Executable (PyInstaller)

**Build:** `python -m PyInstaller launcher.py --onefile --windowed`

**Result:** `launcher.exe` (standalone, includes dependencies)

### Scheduled Task

**Created by:** `create_scheduled_task.ps1`

**Trigger:** Logon event

**Command:** `launcher.exe --profile work`

---

## Dependencies

### Core Dependencies

| Package | Version | Purpose |
|----------|---------|---------|
| pyyaml | 6.0+ | YAML parsing |
| pydantic | 2.0+ | Configuration validation |
| psutil | 5.9+ | Process/network info |
| playwright | 1.40+ | Browser automation |
| pyautogui | 0.9+ | UI automation |
| pystray | 0.19+ | System tray |
| python-dotenv | 1.0+ | Environment variables |
| pywinauto | 0.6+ | Windows automation |

### Development Dependencies

| Package | Purpose |
|----------|---------|
| pytest | Testing framework |
| black | Code formatting |
| ruff | Linting |
| mypy | Type checking |
| pywin32 | Windows Credential Manager |

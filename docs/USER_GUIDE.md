# User Guide

Complete guide for configuring and using Startup Automation.

## Table of Contents

1. [Installation](#installation)
2. [First Run Setup](#first-run-setup)
3. [Profiles](#profiles)
4. [Configuration](#configuration)
5. [Running the Application](#running-the-application)
6. [Command Line Options](#command-line-options)
7. [System Tray](#system-tray)
8. [Metrics](#metrics)
9. [Troubleshooting](#troubleshooting)

---

## Installation

### Prerequisites

- **OS**: Windows 10/11
- **Python**: 3.10 or later
- **PowerShell**: 5.0 or later (recommended for scripts)
- **Administrative privileges**: Required for VPN connections and scheduled tasks

### Setup Steps

1. **Download/Clone** the repository to a permanent location:
   ```powershell
   git clone https://github.com/caprinak/stratup-automation.git
   cd stratup-automation
   ```

2. **Run Setup Script**:
   ```powershell
   .\setup.ps1
   ```

   This script will:
   - Create a Python virtual environment (`venv/`)
   - Install all required dependencies
   - Install Playwright browsers
   - Create necessary directories (`logs/`, `browser_data/`, `profiles/`)

3. **Verify Installation**:
   ```bash
   .\venv\Scripts\python main.py --help
   ```

---

## First Run Setup

### Setting VPN Password

**Option 1: Interactive (Recommended)**
```bash
python main.py --set-password
# You'll be prompted to enter password (hidden input)
```

**Option 2: Command Line**
```bash
python main.py --set-password "your_password_here"
```

**Option 3: Environment Variable (Legacy)**
Create a `.env` file in the project root:
```env
VPN_PASSWORD=your_password_here
```

### Testing Configuration

```bash
# Preview what will happen without executing
python main.py --dry-run
```

---

## Profiles

Profiles allow you to switch between different configurations (work, home, travel).

### Creating Profiles

Create YAML files in the `profiles/` directory:

**Example: `profiles/work.yaml`**
```yaml
general:
  log_level: "INFO"

vpn:
  enabled: true

folders:
  - path: "D:/WorkProjects"

ides:
  - name: "IntelliJ IDEA"
    path: "C:/Tools/idea.exe"
```

**Example: `profiles/home.yaml`**
```yaml
general:
  log_level: "WARNING"

vpn:
  enabled: false

apps:
  - name: "Netflix"
    path: "C:/Users/user/AppData/Local/Netflix/netflix.exe"
```

### Using Profiles

**Command Line:**
```bash
python main.py --profile work
python main.py --profile home
python main.py --profile travel
```

**System Tray:**
Right-click the system tray icon → `👤 Profiles` → Select profile

### Profile Inheritance

Profiles override settings from the base `config.yaml`. This means:
- Common settings go in `config.yaml`
- Profile-specific settings override base config
- You can have multiple profiles without duplicating common config

---

## Configuration

### General Settings

```yaml
general:
  log_level: "INFO"              # DEBUG, INFO, WARNING, ERROR
  log_dir: "logs"               # Directory for log files
  max_retries: 3                 # Max retry attempts for failed operations
  retry_delay: 5                  # Seconds between retries
  parallel_browsers: false        # Launch browsers simultaneously (experimental)
```

### VPN Configuration

```yaml
vpn:
  enabled: true
  name: "MyCorporateVPN"         # Must match Windows VPN name exactly
  type: "forticlient"            # windows, cisco, nordvpn, forticlient
  wait_after_connect: 5            # Seconds to wait for connection
  verify_ip_change: true          # Check if public IP changed after connect
  # password: "Never store here!"  # Use --set-password instead
```

**VPN Types:**

| Type | Description | Requirements |
|-------|-------------|---------------|
| `windows` | Windows built-in VPN | VPN configured in Settings |
| `cisco` | Cisco AnyConnect | `cisco.path` and `cisco.host` set |
| `nordvpn` | NordVPN | NordVPN CLI installed |
| `forticlient` | FortiClient | GUI automation via pywinauto |

### Applications

#### Folders

```yaml
folders:
  - path: "D:/Projects"
    explorer_view: "details"      # details, list, icons, tiles, content
```

#### IDEs

```yaml
ides:
  - name: "IntelliJ IDEA"
    path: "C:/Tools/idea.exe"
    project: "D:/Projects/myproject"
    wait_seconds: 5               # Wait for IDE to fully load
```

#### General Apps

```yaml
apps:
  - name: "VS Code"
    path: "code"                     # Command or absolute path
    args: ["--new-window"]            # Optional: command line arguments
    wait_seconds: 2
    depends_on: []                   # Optional: apps that must start first
    enabled: true
    conditions:                      # Optional: when to launch
      time_range: "9:00-17:00"
      days: "weekdays"
      networks: "OfficeWiFi"
    health_check:                    # Optional: verify launch
      method: "window_title"
      pattern: "Visual Studio Code"
      timeout: 10
      retries: 2
```

**App Dependencies:**

```yaml
apps:
  - name: "Database"
    path: "postgres.exe"
    depends_on: []              # No dependencies, starts first

  - name: "Backend API"
    path: "api.exe"
    depends_on: ["Database"]   # Waits for Database to start

  - name: "Frontend"
    path: "web.exe"
    depends_on: ["Backend API"]  # Waits for Backend API
```

**App Conditions:**

```yaml
apps:
  - name: "Slack"
    conditions:
      time_range: "9:00-17:00"      # Work hours only
      days: "weekdays"                # Mon-Fri only
      networks: "OfficeWiFi,OfficeLAN" # Only on specific network
```

**Health Checks:**

```yaml
apps:
  - name: "VS Code"
    health_check:
      method: "window_title"      # window_title, port, process, none
      pattern: "Visual Studio Code" # Search pattern
      timeout: 10                 # Max wait time (seconds)
      retries: 2                  # Retry attempts
```

**Methods:**
- `window_title`: Check for window matching pattern (default for GUI apps)
- `port`: Check if TCP port is open (for servers)
- `process`: Check if process is running (for background apps)
- `none`: No health check (always succeed)

### Browsers

```yaml
browsers:
  work:
    enabled: true
    browser_type: "chromium"       # chromium, firefox, webkit
    profile_dir: "browser_data/work_profile"
    startup_urls:
      - url: "https://mail.google.com"
        wait_for: "networkidle"    # load, domcontentloaded, networkidle
      - url: "https://calendar.google.com"
        wait_for: "load"
    window:
      width: 1920
      height: 1080
      maximized: true
```

**Wait Strategies:**

| Strategy | Description | Best For |
|----------|-------------|------------|
| `load` | Wait for page load event | Simple pages |
| `domcontentloaded` | Wait for HTML to be parsed | Faster, less reliable | 
| `networkidle` | Wait for network connections to stop | SPAs, Gmail, Jira |
| `commit` | Wait for navigation to commit | Fastest, least reliable |

---

## Running the Application

### System Tray Launcher (Recommended)

Double-click `Startup_Launcher.lnk` to start the system tray service.

**Features:**
- Blue rocket icon in system tray
- Run automation on-demand
- Switch profiles
- View metrics history
- Open logs folder
- Silent operation (no terminal window)

### Manual Execution

```bash
# Activate virtual environment
.\venv\Scripts\activate

# Run main script
python main.py
```

### Scheduled Task (Auto-Start)

To run automatically when you log into Windows:

1. Edit `create_scheduled_task.ps1`
2. Update paths to your installation directory
3. Run as Administrator:
   ```powershell
   Start-Process powershell -Verb RunAs -ArgumentList "create_scheduled_task.ps1"
   ```

---

## Command Line Options

### Basic Options

```bash
python main.py [OPTIONS]

Options:
  -h, --help            Show help message
  -c, --config PATH     Use specific config file (default: config.yaml)
  -p, --profile NAME     Use specific profile (work, home, travel)
  --dry-run              Preview without executing
  --skip-vpn             Skip VPN connection
  --skip-browsers         Skip browser launch
  --browsers-only         Launch browsers only (skip apps and VPN)
```

### Password Management

```bash
python main.py [PASSWORD_OPTIONS]

Password Options:
  --set-password [PWD]    Store VPN password (interactive if PWD omitted)
  --delete-password          Remove VPN password from vault
  --list-passwords           List all stored credentials
```

**Priority Order:** Windows Credential Manager → Environment Variable → Config File

### Metrics

```bash
python main.py --metrics
```

Displays:
- Recent run history (last 10 runs)
- Success rate and average duration
- ASCII chart of performance trends

---

## System Tray

### Menu Options

| Menu Item | Description |
|------------|-------------|
| 🚀 Run Startup Now | Execute full startup sequence |
| 👤 Profiles | Switch between work/home profiles |
| ⚙️ Settings (Open Config) | Open `config.yaml` in default editor |
| 📁 Open Logs | Open `logs/` directory |
| 📊 View Metrics | Show startup performance history |
| ❌ Exit Launcher | Close system tray |

### Profile Switching

Right-click tray icon → `👤 Profiles` → Select profile:
- **Default**: Uses base `config.yaml`
- **Work**: Uses `profiles/work.yaml` merged with base
- **Home**: Uses `profiles/home.yaml` merged with base

---

## Metrics

### Viewing Metrics

```bash
# Command line
python main.py --metrics

# System tray: View Metrics
```

### Metrics Tracked

For each run:
- **Timestamp**: When startup executed
- **Profile**: Which profile was used
- **Duration**: Total time to complete
- **Phase Times**: Duration of each phase
- **Results**: Success/failure of each phase
- **Errors**: Any errors encountered
- **Retries**: Retry counts for each app

### History Storage

Metrics stored in `logs/metrics.jsonl` (newline-delimited JSON):

```json
{"timestamp":"2024-01-18T12:00:00","profile":"work","duration_seconds":45.2,...}
{"timestamp":"2024-01-19T08:30:00","profile":"work","duration_seconds":43.8,...}
```

---

## Troubleshooting

### VPN Issues

**Problem:** VPN not connecting

**Solutions:**
1. Verify VPN name matches Windows Settings exactly
2. Check if VPN client is running
3. Try connecting manually first to verify credentials
4. Use `--skip-vpn` if already connected
5. Check logs in `logs/` for detailed errors

**Problem:** VPN password not working

**Solutions:**
1. Use `--list-passwords` to verify password is stored
2. Delete and re-add: `--delete-password` then `--set-password`
3. Check if password expired in VPN system

### Browser Issues

**Problem:** Browser closes immediately after startup

**Solutions:**
1. Check if another automation tool is interfering
2. Verify `browser_type` matches installed browser
3. Ensure `profile_dir` path is writable
4. Try sequential mode: `parallel_browsers: false`

**Problem:** Specific URL not loading

**Solutions:**
1. Change `wait_for` strategy (try `networkidle` for SPAs)
2. Verify URL is accessible
3. Check if site requires authentication
4. Review browser logs

### Application Issues

**Problem:** App not launching

**Solutions:**
1. Verify path is correct (use absolute paths when possible)
2. Check if app is already running
3. Test manually: run the command directly
4. Check health check pattern matches actual window title

**Problem:** Apps launching in wrong order

**Solutions:**
1. Verify `depends_on` references correct app names
2. Check for circular dependencies
3. Review logs for dependency resolution order

### Config Issues

**Problem:** Validation errors on startup

**Solutions:**
1. Use `--dry-run` to identify issues
2. Check paths exist (or set `enabled: false`)
3. Validate URL formats (must start with http/https)
4. Check for circular dependencies

**Problem:** Apps being skipped unexpectedly

**Solutions:**
1. Check conditions match current state:
   - Current time is within `time_range`
   - Current day matches `days` spec
   - Current network matches `networks`
2. Review logs: skipped apps show reason
3. Try without conditions for testing

### Performance Issues

**Problem:** Startup is slow

**Solutions:**
1. Enable parallel browsers: `parallel_browsers: true`
2. Reduce wait_seconds for apps
3. Optimize wait_for strategies (use `load` instead of `networkidle`)
4. Check metrics for slow phases
5. Disable unused apps or browsers

### Logs

**Log Location:** `logs/` directory

**Log Files:**
- `startup_YYYY-MM-DD.log` - Daily log files
- `metrics.jsonl` - Startup metrics history

**Log Levels:**
- `DEBUG`: Detailed information for troubleshooting
- `INFO`: Normal operation (default)
- `WARNING`: Non-critical issues
- `ERROR`: Failures

### Getting Help

1. Check this user guide
2. Review logs in `logs/` directory
3. Search GitHub issues: https://github.com/caprinak/stratup-automation/issues
4. Create new issue with:
   - Windows version
   - Python version
   - Error messages from logs
   - Steps to reproduce

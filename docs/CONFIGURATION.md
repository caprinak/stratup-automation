# Configuration Reference

Complete reference for all configuration options in `config.yaml` and profile files.

## Table of Contents

1. [General Settings](#general-settings)
2. [VPN Configuration](#vpn-configuration)
3. [Folders](#folders)
4. [IDEs](#ides)
5. [Applications](#applications)
6. [Browsers](#browsers)
7. [Notifications](#notifications)
8. [Profiles](#profiles)

---

## General Settings

```yaml
general:
  # Logging level: DEBUG, INFO, WARNING, ERROR
  log_level: "INFO"

  # Directory for log files and metrics
  log_dir: "logs"

  # Maximum retry attempts for failed operations
  max_retries: 3

  # Seconds between retry attempts
  retry_delay: 5

  # Launch browsers simultaneously (experimental)
  parallel_browsers: false
```

| Setting | Type | Default | Description |
|----------|------|----------|-------------|
| `log_level` | string | "INFO" | Logging verbosity level |
| `log_dir` | string | "logs" | Directory for log files |
| `max_retries` | integer | 3 | Maximum retry attempts (1-10) |
| `retry_delay` | integer | 5 | Seconds between retries (1-60) |
| `parallel_browsers` | boolean | false | Launch browsers in parallel |

---

## VPN Configuration

```yaml
vpn:
  # Enable or disable VPN connection
  enabled: true

  # VPN connection name (must match Windows VPN settings exactly)
  name: "MyCorporateVPN"

  # VPN type: windows, cisco, nordvpn, forticlient
  type: "forticlient"

  # Seconds to wait after attempting connection
  wait_after_connect: 5

  # Verify public IP changed after connecting
  verify_ip_change: true

  # NEVER store password here - use --set-password
  password: null

  # Cisco-specific settings
  cisco:
    path: "C:/Program Files (x86)/Cisco/Cisco AnyConnect Secure Mobility Client/vpncli.exe"
    host: "vpn.company.com"
```

### VPN Types

| Type | Description | Required Fields |
|-------|-------------|-----------------|
| `windows` | Windows built-in VPN | `name` |
| `cisco` | Cisco AnyConnect | `cisco.path`, `cisco.host` |
| `nordvpn` | NordVPN | `name` |
| `forticlient` | FortiClient | `name` |

### Password Priority

1. **Windows Credential Manager** (highest, use `--set-password`)
2. **Environment Variable** (`VPN_PASSWORD`)
3. **Config File** (`vpn.password` - NOT recommended)

---

## Folders

```yaml
folders:
  - path: "C:/Projects"
    explorer_view: "details"
```

| Setting | Type | Values | Description |
|----------|------|---------|-------------|
| `path` | string | - | Folder path (absolute recommended) |
| `explorer_view` | string | details, list, icons, tiles, content | View style for Explorer |

---

## IDEs

```yaml
ides:
  - name: "IntelliJ IDEA"
    path: "C:/Tools/idea.exe"
    project: "D:/Projects/myproject"
    wait_seconds: 5
```

| Setting | Type | Range | Description |
|----------|------|-------|-------------|
| `name` | string | - | IDE display name |
| `path` | string | - | Path to IDE executable or command |
| `project` | string | - | Optional: Path to project file |
| `wait_seconds` | integer | 0-60 | Seconds to wait for IDE to load |

---

## Applications

```yaml
apps:
  - name: "VS Code"
    path: "code"
    args: ["--new-window", "--folder=D:/Projects"]
    wait_seconds: 2
    depends_on: []
    enabled: true
    conditions:
      time_range: "9:00-17:00"
      days: "weekdays"
      networks: "OfficeWiFi"
    health_check:
      method: "window_title"
      pattern: "Visual Studio Code"
      timeout: 10
      retries: 2
```

### App Settings

| Setting | Type | Range | Description |
|----------|------|-------|-------------|
| `name` | string | - | Display name |
| `path` | string | - | Executable path or command |
| `args` | array | - | Command line arguments |
| `wait_seconds` | integer | 0-60 | Seconds to wait after launch |
| `depends_on` | array | - | List of app names to wait for |
| `enabled` | boolean | - | Whether this app launches |

### Conditions

| Setting | Type | Values | Description |
|----------|------|---------|-------------|
| `time_range` | string | "HH:MM-HH:MM" | Time range for launching |
| `days` | string | weekdays, weekends, Mon-Fri, Mon,Wed,Fri | Days to launch |
| `networks` | string | SSID or comma-separated | Networks to launch on |

**Time Range Format:**
- `"9:00-17:00"` - Work hours
- `"0:00-23:59"` - All day

**Days Format:**
- `"weekdays"` - Monday through Friday
- `"weekends"` - Saturday and Sunday
- `"Mon-Fri"` - Range of days
- `"Mon,Wed,Fri"` - Specific days

**Networks Format:**
- `"OfficeWiFi"` - Single network
- `"OfficeWiFi,HomeLAN"` - Multiple networks

### Health Checks

| Setting | Type | Values | Description |
|----------|------|---------|-------------|
| `method` | string | window_title, port, process, none | Check method |
| `pattern` | string | - | Search pattern for window_title/process |
| `timeout` | integer | 1-60 | Seconds to wait for health check |
| `retries` | integer | 0-5 | Retry attempts |

**Health Check Methods:**
- `window_title` - Check for window with matching title (GUI apps)
- `port` - Check if TCP port is open (servers)
- `process` - Check if process is running (background apps)
- `none` - No health check (always succeed)

---

## Browsers

```yaml
browsers:
  work:
    enabled: true
    browser_type: "chromium"
    profile_dir: "browser_data/work_profile"
    startup_urls:
      - url: "https://mail.google.com"
        wait_for: "networkidle"
      - url: "https://calendar.google.com"
        wait_for: "load"
    window:
      width: 1920
      height: 1080
      maximized: true
```

### Browser Settings

| Setting | Type | Range | Values | Description |
|----------|------|-------|---------|-------------|
| `enabled` | boolean | - | Whether this browser launches |
| `browser_type` | string | - | chromium, firefox, webkit |
| `profile_dir` | string | - | Directory for persistent data |
| `maximized` | boolean | - | Start maximized |

### Browser Window

| Setting | Type | Range | Description |
|----------|------|-------|-------------|
| `width` | integer | 800-7680 | Window width |
| `height` | integer | 600-4320 | Window height |

### Startup URLs

| Setting | Type | Values | Description |
|----------|------|---------|-------------|
| `url` | string | http/https URL | URL to open |
| `wait_for` | string | load, domcontentloaded, networkidle, commit | Wait strategy |

**Wait Strategies:**

| Strategy | Description | Best For |
|----------|-------------|------------|
| `load` | Wait for page load event | Simple pages |
| `domcontentloaded` | Wait for HTML to be parsed | Faster, less reliable |
| `networkidle` | Wait for network to settle | SPAs, Gmail, Jira |
| `commit` | Wait for navigation commit | Fastest, least reliable |

---

## Notifications

```yaml
notifications:
  enabled: true
  on_success: true
  on_failure: true
  sound: true
```

| Setting | Type | Default | Description |
|----------|------|----------|-------------|
| `enabled` | boolean | true | Enable/disable notifications |
| `on_success` | boolean | true | Notify on successful startup |
| `on_failure` | boolean | true | Notify on errors |
| `sound` | boolean | true | Play notification sound |

---

## Profiles

Profiles are stored in `profiles/` directory with `.yaml` extension.

### Profile Structure

```yaml
# profiles/work.yaml
general:
  log_level: "DEBUG"

vpn:
  enabled: true

apps:
  - name: "Work Slack"
    conditions:
      networks: "OfficeWiFi"
```

### Profile Inheritance

1. Base config loaded from `config.yaml`
2. Profile settings override base config
3. Lists (apps, folders) are replaced, not merged

### Example Profiles

**Work Profile:**
```yaml
general:
  log_level: "INFO"

vpn:
  enabled: true

folders:
  - path: "D:/Work"

ides:
  - name: "IntelliJ IDEA"
    project: "D:/Work/current"

browsers:
  work:
    enabled: true
    startup_urls:
      - url: "https://work.com"
```

**Home Profile:**
```yaml
general:
  log_level: "WARNING"

vpn:
  enabled: false

folders:
  - path: "D:/Home"

browsers:
  personal:
    enabled: true
    startup_urls:
      - url: "https://youtube.com"
```

---

## Validation Rules

### Configuration Validation

The application validates configuration on startup:

1. **VPN Name Required** - If `vpn.enabled: true`, `vpn.name` must not be empty
2. **URL Format** - All URLs must start with `http://` or `https://`
3. **Dependencies** - All referenced apps must exist
4. **Circular Dependencies** - Detected and reported as errors
5. **Time Range Format** - Must be `HH:MM-HH:MM`
6. **Browser Types** - Must be `chromium`, `firefox`, or `webkit`

### Path Validation

Paths are validated at launch time:
- **Absolute paths** - Checked for existence (can be disabled with `enabled: false`)
- **Relative paths/commands** - Not validated (assume in PATH)
- **Profile directories** - Created automatically if missing

### Health Check Validation

- If `method` is not `none`, `pattern` must not be empty
- `timeout` must be 1-60 seconds
- `retries` must be 0-5 attempts

---

## Examples

### Minimal Config

```yaml
general:
  log_level: "INFO"

vpn:
  enabled: false

folders:
  - path: "C:/Projects"

apps:
  - name: "Notepad++"
    path: "notepad++.exe"
```

### Full Featured Config

```yaml
general:
  log_level: "INFO"
  parallel_browsers: true

vpn:
  enabled: true
  name: "CorporateVPN"
  type: "forticlient"
  wait_after_connect: 10

folders:
  - path: "D:/Projects"
    explorer_view: "details"
  - path: "C:/Users/user/Downloads"

ides:
  - name: "IntelliJ IDEA"
    path: "C:/Tools/idea.exe"
    project: "D:/Projects/main"
    wait_seconds: 10

apps:
  - name: "Database"
    path: "postgres.exe"
    depends_on: []
    health_check:
      method: "port"
      pattern: "5432"
      timeout: 15

  - name: "Backend API"
    path: "api.exe"
    depends_on: ["Database"]
    conditions:
      time_range: "9:00-17:00"
      days: "weekdays"

  - name: "Slack"
    path: "slack.exe"
    conditions:
      networks: "OfficeWiFi"

browsers:
  work:
    enabled: true
    browser_type: "chromium"
    profile_dir: "browser_data/work"
    startup_urls:
      - url: "https://mail.google.com"
        wait_for: "networkidle"
      - url: "https://jira.company.com"
        wait_for: "load"
    window:
      width: 1920
      height: 1080
      maximized: true
```

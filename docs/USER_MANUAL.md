# User Manual - Startup Automation

This manual provides detailed instructions on how to configure, run, and troubleshoot the Startup Automation tool.

## Table of Contents

1. [Installation](#installation)
2. [Configuration Guide](#configuration-guide)
3. [Running the Application](#running-the-application)
4. [Browsers & Profiles](#browsers--profiles)
5. [Troubleshooting](#troubleshooting)

---

## Installation

1.  **Clone/Download** the repository to a permanent location (e.g., `C:\Tools\startup-automation`).
2.  **Open PowerShell** in the directory.
3.  **Run Setup**:
    ```powershell
    .\setup.ps1
    ```
    This script will:
    - Create a Python virtual environment (`venv`).
    - Install necessary Python packages (`playwright`, `pyyaml`, etc.).
    - Install Playwright browsers.
    - Create necessary directories (`logs`, `browser_data`).

---

## Configuration Guide

The `config.yaml` file controls every aspect of the automation.

### General Settings

```yaml
general:
  log_level: "INFO" # DEBUG, INFO, WARNING, ERROR
  parallel_browsers: true # Launch browsers simultaneously (faster) or sequentially
```

### VPN Configuration

If you work remotely, configuring the VPN is critical.

```yaml
vpn:
  enabled: true
  name: "MyCorporateVPN" # Must match Windows VPN setting name
  type: "windows" # 'windows' or 'cisco'
  verify_ip_change: true # Checks if public IP changes after connect
```

### Applications (IDEs & Folders)

Define which tools and folders to open.

```yaml
headers:
  - path: "C:/Projects" # Opens File Explorer

ides:
  - name: "VS Code"
    path: "code" # Command or absolute path to exe
    project: "C:/Projects/frontend"
```

### Browsers

You can define multiple browser profiles (e.g., Work, Personal).

```yaml
browsers:
  work:
    browser_type: "chromium" # chromium, firefox, or webkit
    profile_dir: "browser_data/work_profile" # PERSISTENT data location
    startup_urls:
      - url: "https://gmail.com"
        wait_for: "networkidle" # 'load', 'domcontentloaded', 'networkidle'
```

**Wait Strategies:**

- `load`: Wait for the load event (default).
- `domcontentloaded`: Wait for HTML to be parsed.
- `networkidle`: Wait until network connections stop (good for heavy SPAs).

---

## Running the Application

### System Tray Launcher (Recommended)

Double-click **`Startup_Launcher.lnk`** in the project folder.

- This starts a background process and adds a **blue rocket icon** to your Windows System Tray (bottom right).
- **Right-click** the icon to run the startup sequence, open configuration, or view logs.
- This is the easiest way to use the tool daily without an IDE.

### Manual Run

You can run the script manually at any time:

```bash
.\venv\Scripts\python main.py
```

### Command Line Arguments

- `--dry-run`: Prints what would happen without actually doing it. Useful for testing config changes.
- `--skip-vpn`: Skips the VPN phase. Useful if you are already connected.
- `--browsers-only`: Skips VPN and Apps, launches only browsers.
- `--config my_config.yaml`: Use a specific config file.

### Scheduled Task (Auto-Start)

To have this run automatically when you log in:

1.  Edit `create_scheduled_task.ps1` in a text editor.
2.  **CRITICAL**: Change `"C:\path\to\startup-automation"` to your actual installation path.
3.  Right-click the script and "Run with PowerShell" (Accept Admin prompt).

---

## Browsers & Profiles

This tool uses **Playwright Persistent Contexts**. This means:

- **Cookies are saved**: You won't have to log in to Gmail/Jira every day.
- **Extensions**: You can manually install extensions in the launched browser, and they _should_ persist if they store data in the user directory (though Playwright has some limitations with extensions in automation mode).
- **Keep-Alive**: When the script runs, it launches the browsers and then **stays running**.
  - If you close the command window running the script, the browsers **will close**.
  - **Recommendation**: Let the script run in the background (Window is hidden if run via Task Scheduler properly, or just minimized).

---

## Troubleshooting

### Browser Closes Immediately

- **Cause**: The Python script finished execution.
- **Solution**: The script is designed to stay alive (`while True` loop) if browsers are launched. Ensure you are not forcibly terminating the script (Ctrl+C).

### VPN Fails to Connect

- **Check Name**: Ensure `vpn.name` in `config.yaml` matches exactly what is in Windows Settings > Network & Internet > VPN.
- **Manual Test**: Run `Scripts/connect_vpn.ps1` manually to see detailed PowerShell errors.

### "Playwright not installed"

- Run `playwright install` inside your virtual environment.

### Logs

Check the `logs/` directory. A new log file is created each day (e.g., `startup_2023-10-27.log`).

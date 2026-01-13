# Enhanced Startup Automation

**Startup Automation** is a robust, battle-tested Python application designed to orchestrate your daily Windows startup routine. It handles network connectivity, VPN connections, application launching, and browser sessions with persistent contexts.

## Features

- **🚀 Smart Application Launching**: Open folders, Chrome (with history), Edge, Antigravity, and tools in a specific order.
- **📥 System Tray Launcher**: Run the automation with one click from your Windows Tray.
- **🛡️ Credential Security**: Securely store VPN passwords in a local `.env` file.
- **🌐 Persistence**: Specialized browser launching ensures tabs and sessions stay open after the script ends.
- **⚡ Optimized Sequence**: Applications and browsers open first for an "instant" feel; VPN connects last.
- **📝 Robust Logging**: Detailed rotating logs (`logs/`) to track every action.
- **🔧 Configurable**: Everything is defined in `config.yaml`.

## Quick Start

### 1. Prerequisites

- Windows 10/11
- Python 3.8+
- [Optional] PowerShell 5.0+ (for scripts)

### 2. Setup

Run the included PowerShell setup script to create the environment and install dependencies:

```powershell
.\setup.ps1
```

### 3. Usage

Run the main script:

```bash
python main.py
```

**Options:**

- `python main.py --dry-run` : Preview what will happen without executing.
- `python main.py --skip-vpn` : Skip the VPN connection phase.
- `python main.py --browsers-only` : Only launch browsers.

## Configuration

Edit `config.yaml` to customize your startup:

```yaml
vpn:
  enabled: true
  name: "MyVPN"

browsers:
  work:
    enabled: true
    browser_type: "chromium"
    startup_urls:
      - url: "https://mail.google.com"
```

## Scheduling

To run this automatically when you log in to Windows, edit and run `create_scheduled_task.ps1`:

1.  Open `create_scheduled_task.ps1`
2.  Update the path to your project directory.
3.  Run it as Administrator.

## Documentation

- [User Manual](docs/USER_MANUAL.md) - Detailed configuration and troubleshooting.
- [Technical Docs](docs/TECHNICAL_DOCS.md) - architecture and developer guide.
- [License](LICENSE) - MIT License.

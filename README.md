# Startup Automation

> A powerful Windows startup automation tool that launches VPN, browsers, applications, and folders in the right order with configurable conditions, dependencies, and health checks.

## 🚀 Features

- **Smart Startup**: Launch VPN, browsers, IDEs, and tools in optimal order
- **Multiple Profiles**: Switch between work, home, and travel setups via CLI or system tray
- **App Dependencies**: Automatic topological sorting ensures dependencies launch first
- **Health Checks**: Verify apps launched successfully with automatic retries
- **Conditional Launch**: Skip apps based on time, day of week, or network location
- **Metrics Tracking**: Monitor startup performance over time with ASCII charts
- **Secure Credentials**: Store VPN passwords in Windows Credential Manager (not in plain text)
- **Persistent Browsers**: Keep browser sessions open with Playwright
- **System Tray**: Run in background with easy access to controls

## 📦 Quick Start

### Prerequisites

- Windows 10/11
- Python 3.10+
- Administrative privileges (for VPN and scheduled tasks)

### Installation

```powershell
# Clone or download to a permanent location
git clone https://github.com/caprinak/stratup-automation.git
cd stratup-automation

# Run setup script (creates venv, installs dependencies)
.\setup.ps1

# Set VPN password (secure, stored in Windows Credential Manager)
python main.py --set-password

# Test configuration
python main.py --dry-run

# Run once
python main.py

# Or use system tray launcher (recommended)
.\Startup_Launcher.lnk
```

### Configuration

Edit `config.yaml` to customize your startup:

```yaml
general:
  log_level: "INFO"           # DEBUG, INFO, WARNING, ERROR
  parallel_browsers: false      # Launch browsers simultaneously

vpn:
  enabled: true
  name: "YourVPN"
  type: "forticlient"         # windows, cisco, nordvpn, forticlient

apps:
  - name: "VS Code"
    path: "code"
    project: "C:/Projects"
    depends_on: []             # List of apps this depends on
    enabled: true
    conditions:                # Optional: skip based on conditions
      time_range: "9:00-17:00"  # Work hours
      days: "weekdays"             # weekdays, weekends, or Mon-Fri
      networks: "WorkWiFi"         # WiFi SSID or IP subnet
    health_check:               # Verify app launched
      method: "window_title"      # window_title, port, or none
      pattern: "Visual Studio Code"
      retries: 2
```

### Running

**Command Line Options:**

```bash
# Normal run
python main.py

# Use specific profile
python main.py --profile work

# Dry run (see what would happen)
python main.py --dry-run

# Skip VPN
python main.py --skip-vpn

# Browser only
python main.py --browsers-only

# View metrics history
python main.py --metrics

# Manage VPN password
python main.py --set-password           # Store password interactively
python main.py --set-password "mypassword"  # Store password directly
python main.py --delete-password        # Remove password
python main.py --list-passwords         # List stored credentials
```

**System Tray:**

Right-click the blue rocket icon in your system tray to:
- Run startup now
- Switch profiles (work/home)
- Open configuration
- View logs
- View metrics
- Exit

## 📚 Documentation

- **[User Guide](docs/USER_GUIDE.md)** - Complete usage instructions
- **[Configuration](docs/CONFIGURATION.md)** - Detailed config reference
- **[Architecture](docs/ARCHITECTURE.md)** - System design
- **[Developer Guide](docs/DEVELOPER_GUIDE.md)** - Technical details

## 🔧 Troubleshooting

**VPN not connecting?**
- Verify VPN name matches Windows VPN settings exactly
- Check if VPN client requires additional authentication
- Try connecting manually first
- Use `--skip-vpn` if already connected

**Browser closes immediately?**
- The script uses persistent contexts - browsers should stay open
- Check if another automation tool is interfering
- Review logs in `logs/` directory

**Config validation errors?**
- Use `--dry-run` to test config
- Check paths exist (or set `enabled: false`)
- Validate URL formats
- Check for circular dependencies

**Apps not launching?**
- Check if conditions match current time/day/network
- Verify health check pattern is correct
- Review logs for specific error messages
- Try with `--dry-run` to see which apps are skipped

## 🤝 Contributing

See [DEVELOPER_GUIDE.md](docs/DEVELOPER_GUIDE.md) for contributing guidelines.

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

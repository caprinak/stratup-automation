# Technical Documentation

## Architecture Overview

The application follows a **Phased Execution Model** orchestrated by `main.py`.

```mermaid
graph TD
    Main[main.py] --> Config[Load Config]
    Main --> Logger[Setup Logger]
    Main --> Phase1[Phase 1: System]
    Main --> Phase2[Phase 2: Apps]
    Main --> Phase3[Phase 3: Browsers]
    
    Phase1 --> VPN{VPN Enabled?}
    VPN -- Yes --> ConnectVPN[Powershell Rasdial]
    VPN -- No --> NetCheck[Network Check]
    
    Phase2 --> Explorer[Open Folders]
    Phase2 --> IDE[Launch IDEs (subprocess)]
    
    Phase3 --> Playwright[Init Playwright]
    Playwright --> Context[Launch Persistent Context]
    Context --> Page[Open URLs]
    Phase3 --> KeepAlive[Infinite Loop]
```

## Directory Structure
- `core/`: Shared utilities.
    - `config.py`: Dataclasses for strict typing configuration.
    - `retry.py`: Decorator for exponential backoff.
    - `notifier.py`: PowerShell-based Toast notifications (no extra pip dependencies required for basic toasts, though `win10toast` is listed).
- `phases/`: Logic for each step.
    - `phase1_system.py`: Uses `urllib` for connectivity checks and `subprocess` for VPN commands.
    - `phase3_browsers.py`: The most complex module.

## Deep Dive: Phase 3 (Browsers)

### Why Playwright?
We chose Playwright over Selenium because:
1.  **Speed**: It handles multiple tabs/pages significantly faster.
2.  **Stability**: `wait_for="networkidle"` is much more reliable than sleep-based waits.
3.  **Modern**: Native support for persistent contexts.

### The "Keep-Alive" Mechanism
Playwright's `sync_playwright` manager acts as a server. If the Python process terminates, the Playwright server shuts down, killing all spawned browser processes.

To verify this, `BrowserPhase.run()` implements a **Blocking Loop** at the end of execution:
```python
if launched_any:
    while True:
        time.sleep(1)
```
This ensures that as long as the user wants the browsers open, the script remains active.

### Parallel Execution
When `parallel_browsers: true` is set, `ThreadPoolExecutor` is used.
**Note**: Playwright is not thread-safe if sharing the same `playwright` object across threads for *creation* sometimes, but separate contexts are usually fine. The implementation launches separate browser instances serially or in parallel threads. Be cautious with high concurrency on low-resource machines.

## Extending the Application

### Adding a New Phase
1.  Create `phases/phase4_custom.py`.
2.  Define a class with a `run()` method.
3.  Import and instantiate it in `main.py`.

### Custom VPN Support
Modify `phases/phase1_system.py` method `_connect_vpn`. You can add support for OpenVPN or WireGuard by invoking their CLI tools via `subprocess`.

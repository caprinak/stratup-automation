"""
Phase 2: Application startup - Folders, IDEs, tools
"""
import subprocess
import time
from pathlib import Path
from typing import List, Set, Dict
from collections import defaultdict, deque

import subprocess
import time
from pathlib import Path
from typing import List, Set, Dict
from collections import defaultdict, deque
import pyautogui
import pygetwindow as gw

from core.config import Config, FolderConfig, IDEConfig, GeneralAppConfig
from core.logger import get_logger
from core.conditions import should_launch_app


class AppsPhase:
    """Handle application startup tasks."""
    
    def __init__(self, config: Config):
        self.config = config
        self.logger = get_logger()
        self.launched_apps: Set[str] = set()
    
    def run(self) -> bool:
        """Execute all application phase tasks."""
        self.logger.info("=" * 50)
        self.logger.info("PHASE 2: Applications")
        self.logger.info("=" * 50)
        
        try:
            # 1. Open folders
            self.open_folders()
            
            # 2. Launch IDEs
            self.launch_ides()
            
            # 3. Launch General Apps (with dependency resolution)
            self.launch_apps()
            
            self.logger.info("Phase 2 completed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Phase 2 failed: {e}")
            raise
    
    def open_folders(self):
        """Open all configured folders in Explorer."""
        if not self.config.folders:
            self.logger.info("No folders configured")
            return
        
        self.logger.info(f"Opening {len(self.config.folders)} folders...")
        
        for folder in self.config.folders:
            self._open_folder(folder)
    
    def _open_folder(self, folder: FolderConfig):
        """Open a single folder in Explorer."""
        path = Path(folder.path)
        
        if not path.exists():
            self.logger.warning(f"Folder not found: {folder.path}")
            return
        
        try:
            subprocess.Popen(
                ["explorer", str(path)],
                shell=True
            )
            self.logger.info(f"[OK] Opened: {folder.path}")
            time.sleep(0.5)  # Brief delay between windows
            
        except Exception as e:
            self.logger.error(f"Failed to open {folder.path}: {e}")
    
    def launch_ides(self):
        """Launch all configured IDEs."""
        if not self.config.ides:
            self.logger.info("No IDEs configured")
            return
        
        self.logger.info(f"Launching {len(self.config.ides)} IDEs...")
        
        for ide in self.config.ides:
            self._launch_ide(ide)
    
    def _launch_ide(self, ide: IDEConfig):
        """Launch a single IDE."""
        try:
            # Build command
            cmd = [ide.path]
            if ide.project:
                cmd.append(ide.project)
            
            # Check if path exists (if absolute path)
            if Path(ide.path).is_absolute() and not Path(ide.path).exists():
                self.logger.warning(f"IDE not found: {ide.path}")
                return
            
            # Launch IDE
            subprocess.Popen(
                cmd,
                shell=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            
            self.logger.info(f"[OK] Launched: {ide.name}")
            
            # Wait for IDE to initialize
            if ide.wait_seconds > 0:
                self.logger.debug(f"Waiting {ide.wait_seconds}s for {ide.name}...")
                time.sleep(ide.wait_seconds)
            
        except Exception as e:
            self.logger.error(f"Failed to launch {ide.name}: {e}")

    def launch_apps(self):
        """Launch general applications with dependency resolution."""
        if not self.config.apps:
            self.logger.info("No general apps configured")
            return
        
        # Filter enabled apps
        enabled_apps = [app for app in self.config.apps if app.enabled]
        if not enabled_apps:
            self.logger.info("No enabled general apps")
            return
        
        # Filter by conditions
        apps_to_launch = []
        for app in enabled_apps:
            if should_launch_app(app.conditions):
                apps_to_launch.append(app)
            else:
                self.logger.info(f"[SKIP] {app.name} (conditions not met)")
        
        if not apps_to_launch:
            self.logger.info("No apps matching current conditions")
            return
        
        self.logger.info(f"Launching {len(apps_to_launch)} general apps (with dependencies and conditions)...")
        
        # Get launch order with topological sort
        launch_order = self._get_launch_order(apps_to_launch)
        
        # Launch apps in order
        for app_name in launch_order:
            app = next((a for a in apps_to_launch if a.name == app_name), None)
            if app:
                self._launch_app(app)
    
    def _get_launch_order(self, apps: List[GeneralAppConfig]) -> List[str]:
        """
        Get launch order using topological sort to respect dependencies.
        
        Args:
            apps: List of apps to sort
            
        Returns:
            List of app names in dependency order
        """
        # Build dependency graph
        graph: Dict[str, Set[str]] = defaultdict(set)
        in_degree: Dict[str, int] = {}
        
        # Initialize graph
        for app in apps:
            graph[app.name] = set()
            in_degree[app.name] = 0
        
        # Add edges (dependencies)
        for app in apps:
            for dep in app.depends_on:
                # Only add dependency if it exists in the app list
                if dep in graph:
                    graph[dep].add(app.name)
                    in_degree[app.name] += 1
                else:
                    self.logger.warning(f"App '{app.name}' depends on unknown app '{dep}', ignoring")
        
        # Topological sort using Kahn's algorithm
        queue = deque([app.name for app in apps if in_degree[app.name] == 0])
        launch_order = []
        
        while queue:
            current = queue.popleft()
            launch_order.append(current)
            
            for dependent in graph[current]:
                in_degree[dependent] -= 1
                if in_degree[dependent] == 0:
                    queue.append(dependent)
        
        # Check for cycles (shouldn't happen if validation is working)
        if len(launch_order) != len(apps):
            self.logger.warning("Possible circular dependency detected, some apps may not launch")
            # Add remaining apps
            for app in apps:
                if app.name not in launch_order:
                    launch_order.append(app.name)
        
        return launch_order

    def _launch_app(self, app: GeneralAppConfig):
        """Launch a single general application with health checks and retries."""
        max_attempts = app.health_check.retries + 1
        
        for attempt in range(max_attempts):
            try:
                # Build command string for shell execution to handle spaces properly
                cmd_str = f'"{app.path}" ' + " ".join(app.args)
                
                # Check if path exists (if absolute path)
                if Path(app.path).is_absolute() and not Path(app.path).exists():
                    self.logger.warning(f"App not found: {app.path}")
                    return
                
                # Launch App
                subprocess.Popen(
                    cmd_str,
                    shell=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS if hasattr(subprocess, 'CREATE_NEW_PROCESS_GROUP') else 0
                )
                
                attempt_msg = f" (attempt {attempt + 1}/{max_attempts})" if max_attempts > 1 else ""
                self.logger.info(f"[OK] Launched: {app.name}{attempt_msg}")
                
                # Wait for app to initialize
                wait_time = app.wait_seconds + (app.health_check.timeout if app.health_check.method != "none" else 0)
                if wait_time > 0:
                    self.logger.debug(f"Waiting {wait_time}s for {app.name}...")
                    time.sleep(wait_time)
                
                # Perform health check if configured
                if app.health_check.method != "none":
                    if self._perform_health_check(app):
                        self.launched_apps.add(app.name)
                        # SPECIAL HANDLING: Force Chrome session restore
                        if "chrome" in app.name.lower() or "chrome.exe" in app.path.lower():
                            self._restore_chrome_session()
                        break
                    else:
                        if attempt < max_attempts - 1:
                            self.logger.warning(f"Health check failed for {app.name}, retrying...")
                            time.sleep(2)
                        else:
                            self.logger.error(f"Health check failed for {app.name} after {max_attempts} attempts")
                else:
                    self.launched_apps.add(app.name)
                    # SPECIAL HANDLING: Force Chrome session restore
                    if "chrome" in app.name.lower() or "chrome.exe" in app.path.lower():
                        self._restore_chrome_session()
                    break

            except Exception as e:
                self.logger.error(f"Failed to launch {app.name}: {e}")
                if attempt < max_attempts - 1:
                    time.sleep(2)
    
    def _perform_health_check(self, app: GeneralAppConfig) -> bool:
        """
        Perform health check for an application.
        
        Args:
            app: Application configuration
            
        Returns:
            True if health check passes, False otherwise
        """
        method = app.health_check.method
        pattern = app.health_check.pattern
        
        if method == "window_title":
            return self._check_window_title(pattern)
        elif method == "port":
            return self._check_port(pattern)
        elif method == "process":
            return self._check_process(pattern)
        else:
            return True  # No health check means always pass
    
    def _check_window_title(self, pattern: str) -> bool:
        """Check if a window with matching title exists."""
        try:
            import re
            windows = gw.getWindowsWithTitle(pattern)
            
            # Try pattern matching if no exact match found
            if not windows:
                all_windows = gw.getAllWindows()
                pattern_re = re.compile(pattern, re.IGNORECASE)
                windows = [w for w in all_windows if w.title and pattern_re.search(w.title)]
            
            if windows:
                self.logger.debug(f"[OK] Found window matching '{pattern}': {windows[0].title}")
                return True
            else:
                self.logger.warning(f"[FAIL] No window found matching '{pattern}'")
                return False
        except Exception as e:
            self.logger.warning(f"Window title health check failed: {e}")
            return False
    
    def _check_port(self, port: str) -> bool:
        """Check if a port is open."""
        try:
            import socket
            port_num = int(port)
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex(('127.0.0.1', port_num))
            sock.close()
            
            if result == 0:
                self.logger.debug(f"[OK] Port {port} is open")
                return True
            else:
                self.logger.warning(f"[FAIL] Port {port} is not open")
                return False
        except Exception as e:
            self.logger.warning(f"Port health check failed: {e}")
            return False
    
    def _check_process(self, process_name: str) -> bool:
        """Check if a process is running."""
        try:
            import psutil
            for proc in psutil.process_iter(['name']):
                if process_name.lower() in proc.info['name'].lower():
                    self.logger.debug(f"[OK] Found process: {proc.info['name']}")
                    return True
            self.logger.warning(f"[FAIL] Process '{process_name}' not found")
            return False
        except Exception as e:
            self.logger.warning(f"Process health check failed: {e}")
            return False
    
    def _restore_chrome_session(self):
        """Send Ctrl+Shift+T to restore Chrome session."""
        try:
            self.logger.info("Sending Ctrl+Shift+T to restore Chrome session...")
            time.sleep(2)
            
            chrome_windows = [w for w in gw.getWindowsWithTitle('Chrome') if w.title]
            if chrome_windows:
                try:
                    w = chrome_windows[0]
                    if w.isMinimized:
                        w.restore()
                    w.activate()
                    time.sleep(0.5)
                except:
                    pass
            
            pyautogui.hotkey('ctrl', 'shift', 't')
            self.logger.info("[OK] Session restore shortcut sent")
        except Exception as e:
            self.logger.warning(f"Failed to restore Chrome session: {e}")

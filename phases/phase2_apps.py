"""
Phase 2: Application startup - Folders, IDEs, tools
"""
import subprocess
import time
from pathlib import Path
from typing import List

from core.config import Config, FolderConfig, IDEConfig
from core.logger import get_logger


class AppsPhase:
    """Handle application startup tasks."""
    
    def __init__(self, config: Config):
        self.config = config
        self.logger = get_logger()
    
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
            self.logger.info(f"✓ Opened: {folder.path}")
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
            
            self.logger.info(f"✓ Launched: {ide.name}")
            
            # Wait for IDE to initialize
            if ide.wait_seconds > 0:
                self.logger.debug(f"Waiting {ide.wait_seconds}s for {ide.name}...")
                time.sleep(ide.wait_seconds)
            
        except Exception as e:
            self.logger.error(f"Failed to launch {ide.name}: {e}")

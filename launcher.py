import os
import sys
import threading
from pathlib import Path
from typing import Optional
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageDraw
import pystray
from pystray import MenuItem as item

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from main import main as run_automation

class StartupLauncher:
    def __init__(self):
        self.icon = None
        self.running = False
        
    def create_image(self):
        # Create a simple icon: a blue circle on a transparent background
        width = 64
        height = 64
        color1 = (41, 121, 255) # Modern Blue
        color2 = (255, 255, 255) # White
        
        image = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        dc = ImageDraw.Draw(image)
        
        # Draw a stylized "A" or just a rocket/circle
        dc.ellipse([4, 4, 60, 60], fill=color1)
        dc.polygon([32, 10, 50, 50, 14, 50], fill=color2) # Simple triangle/rocket
        
        return image

    def on_launch(self, icon, item):
        if self.running:
            return
            
        self.running = True
        icon.title = "Startup Automation: Running..."
        
        # Run in a separate thread to keep UI responsive
        thread = threading.Thread(target=self._execute_automation)
        thread.daemon = True
        thread.start()

    def _execute_automation(self):
        try:
            # Mock sys.argv for main()
            sys.argv = [sys.argv[0]] 
            run_automation()
        except Exception as e:
            # Simple error notification using tkinter (minimal)
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror("Startup Error", str(e))
            root.destroy()
        finally:
            self.running = False
            if self.icon:
                self.icon.title = "Startup Automation: Ready"

    def on_quit(self, icon, item):
        icon.stop()

    def run(self):
        image = self.create_image()
        menu = (
            item('🚀 Run Startup Now', self.on_launch, default=True),
            item('⚙️ Settings (Open Config)', lambda: os.startfile("config.yaml")),
            item('👤 Profiles', self._get_profile_menu()),
            item('📁 Open Logs', lambda: os.startfile("logs")),
            item('❌ Exit Launcher', self.on_quit)
        )
        
        self.icon = pystray.Icon("startup_automation", image, "Startup Automation: Ready", menu)
        self.icon.run()

    def _get_profile_menu(self):
        """Get profile selector submenu."""
        profiles_dir = Path("profiles")
        profiles = []
        
        if profiles_dir.exists():
            for profile_file in sorted(profiles_dir.glob("*.yaml")):
                profile_name = profile_file.stem
                profiles.append(
                    item(f'📋 {profile_name}', 
                         lambda p=profile_name: self._launch_with_profile(p))
                )
        
        if not profiles:
            profiles.append(item('📋 Default', lambda: self._launch_with_profile(None)))
        
        return tuple(profiles)

    def _launch_with_profile(self, profile: Optional[str]):
        """Run automation with specified profile."""
        if self.running:
            return
            
        self.running = True
        if self.icon:
            self.icon.title = f"Startup Automation: Running{' (' + profile + ')' if profile else ''}..."
        
        def run_with_profile():
            try:
                from core.config import load_config
                config = load_config(profile=profile)
                
                from phases.phase2_apps import AppsPhase
                from phases.phase3_browsers import BrowserPhase
                from phases.phase1_system import SystemPhase
                
                results = {"phase1": False, "phase2": False, "phase3": False}
                
                # Phase 2: Applications
                try:
                    phase2 = AppsPhase(config)
                    results["phase2"] = phase2.run()
                except Exception as e:
                    pass
                
                # Phase 3: Browsers
                try:
                    phase3 = BrowserPhase(config)
                    results["phase3"] = phase3.run()
                except Exception as e:
                    pass
                
                # Phase 1: System tasks (VPN)
                if not profile or any(["skip_vpn" not in str(profile), True]):
                    try:
                        phase1 = SystemPhase(config)
                        results["phase1"] = phase1.run()
                    except Exception as e:
                        pass
                
            except Exception as e:
                pass
            finally:
                self.running = False
                if self.icon:
                    self.icon.title = "Startup Automation: Ready"
        
        thread = threading.Thread(target=run_with_profile)
        thread.daemon = True
        thread.start()

if __name__ == "__main__":
    launcher = StartupLauncher()
    launcher.run()

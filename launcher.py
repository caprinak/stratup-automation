import os
import sys
import threading
from pathlib import Path
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
            item('📁 Open Logs', lambda: os.startfile("logs")),
            item('❌ Exit Launcher', self.on_quit)
        )
        
        self.icon = pystray.Icon("startup_automation", image, "Startup Automation: Ready", menu)
        self.icon.run()

if __name__ == "__main__":
    launcher = StartupLauncher()
    launcher.run()

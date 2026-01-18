"""
Phase 3: Browser automation with Playwright
Uses PERSISTENT context to keep browsers open after script ends
"""
import time
from pathlib import Path
from typing import Dict, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

from playwright.sync_api import sync_playwright, Browser, BrowserContext, Page

from core.config import Config, BrowserConfig
from core.logger import get_logger
from core.retry import retry


class BrowserPhase:
    """Handle browser startup with Playwright."""
    
    def __init__(self, config: Config):
        self.config = config
        self.logger = get_logger()
    
    def run(self) -> bool:
        """Execute all browser phase tasks."""
        self.logger.info("=" * 50)
        self.logger.info("PHASE 3: Browsers")
        self.logger.info("=" * 50)
        
        enabled_browsers = {
            name: cfg 
            for name, cfg in self.config.browsers.items() 
            if cfg.enabled
        }
        
        if not enabled_browsers:
            self.logger.info("No browsers enabled")
            return True
        
        try:
            if self.config.parallel_browsers:
                self._launch_parallel(enabled_browsers)
            else:
                self._launch_sequential(enabled_browsers)
            
            self.logger.info("Phase 3 completed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Phase 3 failed: {e}")
            raise
    
    def _launch_sequential(self, browsers: Dict[str, BrowserConfig]):
        """Launch browsers one by one."""
        for name, browser_config in browsers.items():
            self._launch_browser(name, browser_config)
    
    def _launch_parallel(self, browsers: Dict[str, BrowserConfig]):
        """Launch browsers in parallel."""
        with ThreadPoolExecutor(max_workers=len(browsers)) as executor:
            futures = {
                executor.submit(self._launch_browser, name, cfg): name
                for name, cfg in browsers.items()
            }
            
            for future in as_completed(futures):
                name = futures[future]
                try:
                    future.result()
                except Exception as e:
                    self.logger.error(f"Browser {name} failed: {e}")
    
    @retry(max_attempts=2, delay=3)
    def _launch_browser(self, name: str, browser_config: BrowserConfig):
        """
        Launch a browser with persistent context.
        
        CRITICAL: Uses launch_persistent_context so browser stays open
        after the Python script exits.
        """
        self.logger.info(f"Launching browser: {name}")
        
        # Ensure profile directory exists
        profile_dir = Path(browser_config.profile_dir)
        profile_dir.mkdir(parents=True, exist_ok=True)
        
        with sync_playwright() as p:
            # Get browser type
            browser_type = getattr(p, browser_config.browser_type)
            
            # Launch with persistent context
            # This keeps the browser open after script ends!
            context = browser_type.launch_persistent_context(
                user_data_dir=str(profile_dir.absolute()),
                headless=False,
                viewport={
                    "width": browser_config.window.width,
                    "height": browser_config.window.height
                },
                args=[
                    "--start-maximized" if browser_config.window.maximized else "",
                    "--disable-blink-features=AutomationControlled",
                ],
                ignore_default_args=["--enable-automation"],
            )
            
            # Open URLs in tabs
            self._open_urls_in_tabs(context, browser_config, name)
            
            # IMPORTANT: Don't close context!
            # Detach from it so browser stays open
            self.logger.info(f"[OK] Browser {name} launched with {len(browser_config.startup_urls)} tabs")
            
            # Small delay before detaching
            time.sleep(2)
    
    def _open_urls_in_tabs(
        self,
        context: BrowserContext,
        browser_config: BrowserConfig,
        name: str
    ):
        """Open all URLs in separate tabs."""
        
        pages = context.pages
        
        for i, url_config in enumerate(browser_config.startup_urls):
            try:
                # Use existing page or create new one
                if i < len(pages):
                    page = pages[i]
                else:
                    page = context.new_page()
                
                self.logger.debug(f"[{name}] Opening: {url_config.url}")
                
                page.goto(
                    url_config.url,
                    wait_until=url_config.wait_for,
                    timeout=30000
                )
                
                self.logger.info(f"  [OK] {url_config.url}")
                
            except Exception as e:
                self.logger.warning(f"  ✗ Failed to load {url_config.url}: {e}")

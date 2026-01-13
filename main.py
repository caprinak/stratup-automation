#!/usr/bin/env python3
"""
Windows Startup Automation Orchestrator

This script coordinates all startup tasks:
1. System: Network check, VPN connection
2. Apps: Folders, IDEs, tools
3. Browsers: Work and personal with persistent sessions

Usage:
    python main.py                    # Run all phases
    python main.py --skip-vpn         # Skip VPN connection
    python main.py --browsers-only    # Only launch browsers
    python main.py --dry-run          # Show what would be done
"""
import sys
import time
import argparse
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from core.config import load_config, Config
from core.logger import setup_logger, get_logger
from core.notifier import Notifier

from phases.phase1_system import SystemPhase
from phases.phase2_apps import AppsPhase
from phases.phase3_browsers import BrowserPhase


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Windows Startup Automation"
    )
    
    parser.add_argument(
        "--config", "-c",
        default="config.yaml",
        help="Path to config file"
    )
    
    parser.add_argument(
        "--skip-vpn",
        action="store_true",
        help="Skip VPN connection"
    )
    
    parser.add_argument(
        "--skip-browsers",
        action="store_true",
        help="Skip browser launch"
    )
    
    parser.add_argument(
        "--browsers-only",
        action="store_true",
        help="Only launch browsers"
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without executing"
    )
    
    return parser.parse_args()


def main():
    """Main orchestration function."""
    args = parse_args()
    start_time = datetime.now()
    
    # Load configuration
    try:
        config = load_config(args.config)
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        sys.exit(1)
    
    # Apply CLI overrides
    if args.skip_vpn:
        config.vpn.enabled = False
    
    # Setup logging
    logger = setup_logger(
        name="startup",
        log_dir=config.log_dir,
        level=config.log_level
    )
    
    # Setup notifications
    notifier = Notifier(enabled=config.notifications_enabled)
    
    logger.info("=" * 60)
    logger.info("  WINDOWS STARTUP AUTOMATION")
    logger.info(f"  Started: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 60)
    
    if args.dry_run:
        logger.info("[DRY RUN MODE - No actions will be performed]")
        _show_plan(config, args)
        return
    
    # Track results
    results = {"phase1": False, "phase2": False, "phase3": False}
    errors = []
    
    try:
        # Phase 2: Applications
        if not args.browsers_only:
            try:
                phase2 = AppsPhase(config)
                results["phase2"] = phase2.run()
            except Exception as e:
                errors.append(f"Phase 2: {e}")
                logger.error(f"Phase 2 error: {e}")
        
        # Phase 3: Browsers
        if not args.skip_browsers:
            try:
                phase3 = BrowserPhase(config)
                results["phase3"] = phase3.run()
            except Exception as e:
                errors.append(f"Phase 3: {e}")
                logger.error(f"Phase 3 error: {e}")

        # Phase 1: System tasks (VPN) - Moved to last stage
        if not args.browsers_only and not args.skip_vpn:
            try:
                phase1 = SystemPhase(config)
                results["phase1"] = phase1.run()
            except Exception as e:
                errors.append(f"Phase 1: {e}")
                logger.error(f"Phase 1 error: {e}")
        
        # Summary
        elapsed = (datetime.now() - start_time).total_seconds()
        logger.info("=" * 60)
        logger.info("  STARTUP COMPLETE")
        logger.info(f"  Duration: {elapsed:.1f} seconds")
        logger.info(f"  Results: {results}")
        logger.info("=" * 60)
        
        if errors:
            notifier.warning(f"Completed with {len(errors)} error(s)")
        else:
            notifier.success(f"All systems ready in {elapsed:.0f}s")
    
    except KeyboardInterrupt:
        logger.warning("Startup interrupted by user")
        notifier.warning("Startup cancelled")
        sys.exit(1)
    
    except Exception as e:
        logger.exception(f"Fatal error: {e}")
        notifier.error(str(e))
        sys.exit(1)


def _show_plan(config: Config, args):
    """Show what would be executed in dry-run mode."""
    logger = get_logger()
    
    logger.info("\n[EXECUTION PLAN]")
    
    if not args.browsers_only:
        logger.info("\nPhase 1 - System:")
        logger.info(f"  • Network check: {config.network_check_url}")
        if config.vpn.enabled:
            logger.info(f"  • VPN connect: {config.vpn.name} ({config.vpn.type})")
        else:
            logger.info("  • VPN: Disabled")
        
        logger.info("\nPhase 2 - Applications:")
        for folder in config.folders:
            logger.info(f"  • Open folder: {folder.path}")
        for ide in config.ides:
            logger.info(f"  • Launch IDE: {ide.name}")
        for app in config.apps:
            logger.info(f"  • Launch App: {app.name}")
    
    if not args.skip_browsers:
        logger.info("\nPhase 3 - Browsers:")
        for name, browser in config.browsers.items():
            if browser.enabled:
                logger.info(f"  • {name} browser ({browser.browser_type}):")
                for url in browser.startup_urls:
                    logger.info(f"      - {url.url}")


if __name__ == "__main__":
    main()

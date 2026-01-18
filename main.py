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
from core.metrics import MetricsTracker, format_ascii_chart


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
        "--profile", "-p",
        default=None,
        help="Profile name to load (e.g., work, home, travel)"
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
    
    parser.add_argument(
        "--set-password",
        nargs="?",
        const=True,
        metavar="PASSWORD",
        help="Store VPN password in Windows Credential Manager. If no password is provided, prompts for input."
    )
    
    parser.add_argument(
        "--delete-password",
        action="store_true",
        help="Delete VPN password from Windows Credential Manager"
    )
    
    parser.add_argument(
        "--list-passwords",
        action="store_true",
        help="List all stored passwords in vault"
    )
    
    parser.add_argument(
        "--metrics",
        action="store_true",
        help="View startup metrics history"
    )
    
    return parser.parse_args()


def main():
    """Main orchestration function."""
    args = parse_args()
    start_time = datetime.now()
    
    # Handle password management commands
    if args.list_passwords:
        from core.vault import VaultManager
        services = VaultManager.list_credentials()
        if services:
            print("Stored credentials:")
            for service in services:
                print(f"  - {service}")
        else:
            print("No credentials stored.")
        return
    
    if args.delete_password:
        from core.vault import delete_vpn_password
        if delete_vpn_password():
            print("VPN password deleted from vault")
        else:
            print("Failed to delete VPN password")
        return
    
    if args.set_password is not None:
        from core.vault import set_vpn_password, delete_vpn_password
        import getpass
        
        # Get password
        if args.set_password is True:
            password = getpass.getpass("Enter VPN password (hidden): ")
            confirm = getpass.getpass("Confirm password: ")
            if password != confirm:
                print("Passwords do not match")
        else:
            password = args.set_password
        
        # Delete existing first
        delete_vpn_password()
        
        # Store new password
        if set_vpn_password(password):
            print("VPN password stored in Windows Credential Manager")
        else:
            print("Failed to store VPN password")
        return
    
    # Load configuration
    try:
        config = load_config(args.config, profile=args.profile)
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        sys.exit(1)
    except ValueError as e:
        print(f"CONFIG ERROR: {e}")
        sys.exit(1)
    
    # Initialize metrics tracking
    metrics_tracker = MetricsTracker(config.log_dir)
    metrics = metrics_tracker.start(profile=args.profile)
    
    # Handle metrics view command
    if args.metrics:
        print(metrics_tracker.format_history())
        print()
        print(metrics_tracker.format_summary())
        print(format_ascii_chart(metrics_tracker.get_history(limit=20)))
        return
    
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
            phase2_start = datetime.now()
            try:
                phase2 = AppsPhase(config)
                results["phase2"] = phase2.run()
                phase2_duration = (datetime.now() - phase2_start).total_seconds()
                metrics.record_phase("phase2", phase2_duration, results["phase2"])
            except Exception as e:
                errors.append(f"Phase 2: {e}")
                logger.error(f"Phase 2 error: {e}")
                metrics.record_phase("phase2", 0, False)
                metrics.add_error(f"Phase 2: {e}")
        
        # Phase 3: Browsers
        if not args.skip_browsers:
            phase3_start = datetime.now()
            try:
                phase3 = BrowserPhase(config)
                results["phase3"] = phase3.run()
                phase3_duration = (datetime.now() - phase3_start).total_seconds()
                metrics.record_phase("phase3", phase3_duration, results["phase3"])
            except Exception as e:
                errors.append(f"Phase 3: {e}")
                logger.error(f"Phase 3 error: {e}")
                metrics.record_phase("phase3", 0, False)
                metrics.add_error(f"Phase 3: {e}")

        # Phase 1: System tasks (VPN) - Moved to last stage
        if not args.browsers_only and not args.skip_vpn:
            phase1_start = datetime.now()
            try:
                phase1 = SystemPhase(config)
                results["phase1"] = phase1.run()
                phase1_duration = (datetime.now() - phase1_start).total_seconds()
                metrics.record_phase("phase1", phase1_duration, results["phase1"])
            except Exception as e:
                errors.append(f"Phase 1: {e}")
                logger.error(f"Phase 1 error: {e}")
                metrics.record_phase("phase1", 0, False)
                metrics.add_error(f"Phase 1: {e}")
        
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
        
        # Save metrics
        if not args.dry_run:
            metrics.save(config.log_dir)
            logger.info("✓ Metrics recorded")
    
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

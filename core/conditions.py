"""
Condition evaluator for conditional app launching
"""
import re
import socket
import ipaddress
from datetime import datetime
from typing import Dict, Optional
import psutil


class ConditionEvaluator:
    """Evaluates conditions for app launching"""
    
    @staticmethod
    def evaluate(conditions: Optional[Dict[str, str]]) -> bool:
        """
        Evaluate if conditions are met for launching an app.
        
        Args:
            conditions: Dictionary of conditions (time_range, days, networks)
            
        Returns:
            True if all conditions are met, False otherwise
        """
        if not conditions:
            return True
        
        # If any condition is specified, it must pass
        has_conditions = False
        
        # Time range condition
        if "time_range" in conditions:
            has_conditions = True
            if not ConditionEvaluator._evaluate_time_range(conditions["time_range"]):
                return False
        
        # Days condition
        if "days" in conditions:
            has_conditions = True
            if not ConditionEvaluator._evaluate_days(conditions["days"]):
                return False
        
        # Networks condition
        if "networks" in conditions:
            has_conditions = True
            if not ConditionEvaluator._evaluate_networks(conditions["networks"]):
                return False
        
        # If no actual conditions were specified, default to True
        return has_conditions
    
    @staticmethod
    def _evaluate_time_range(time_range: str) -> bool:
        """
        Evaluate if current time is within specified range.
        
        Args:
            time_range: Time range in format "HH:MM-HH:MM" or "9:00-17:00"
            
        Returns:
            True if current time is within range
        """
        try:
            now = datetime.now()
            current_minutes = now.hour * 60 + now.minute
            
            start, end = time_range.split("-")
            
            def time_to_minutes(time_str: str) -> int:
                h, m = map(int, time_str.split(":"))
                return h * 60 + m
            
            start_minutes = time_to_minutes(start)
            end_minutes = time_to_minutes(end)
            
            return start_minutes <= current_minutes <= end_minutes
        except Exception:
            return False
    
    @staticmethod
    def _evaluate_days(days_spec: str) -> bool:
        """
        Evaluate if current day matches specification.
        
        Args:
            days_spec: Days in format "Mon-Fri" or "Mon,Wed,Fri" or "weekdays" or "weekends"
            
        Returns:
            True if current day matches
        """
        current_day = datetime.now().strftime("%a")  # Mon, Tue, Wed, etc.
        day_num = datetime.now().weekday()  # 0-6 (Mon-Sun)
        
        try:
            days_spec = days_spec.lower()
            
            # Handle keywords
            if days_spec == "weekdays":
                return day_num < 5  # Mon-Fri
            elif days_spec == "weekends":
                return day_num >= 5  # Sat-Sun
            
            # Handle range "Mon-Fri"
            if "-" in days_spec and "," not in days_spec:
                day_map = {"mon": 0, "tue": 1, "wed": 2, "thu": 3, "fri": 4, "sat": 5, "sun": 6}
                start_day, end_day = days_spec.lower().split("-")
                if start_day in day_map and end_day in day_map:
                    return day_map[start_day] <= day_num <= day_map[end_day]
            
            # Handle list "Mon,Wed,Fri"
            if "," in days_spec:
                allowed_days = [d.lower().strip() for d in days_spec.split(",")]
                return current_day.lower() in allowed_days
            
            # Handle single day "Mon"
            return current_day.lower() == days_spec.lower()
            
        except Exception:
            return False
    
    @staticmethod
    def _evaluate_networks(networks_spec: str) -> bool:
        """
        Evaluate if current network matches specification.
        
        Args:
            networks_spec: Comma-separated list of network names (SSIDs) or IP ranges
            
        Returns:
            True if current network matches
        """
        try:
            allowed_networks = [n.strip().lower() for n in networks_spec.split(",")]
            current_network = ConditionEvaluator._get_current_network()
            
            if not current_network:
                return False
            
            return current_network.lower() in allowed_networks
        except Exception:
            return False
    
    @staticmethod
    def _get_current_network() -> Optional[str]:
        """
        Get current network identifier.
        
        Returns:
            SSID (if on WiFi) or IP range, or None if unable to determine
        """
        try:
            # Try to get WiFi SSID on Windows
            import subprocess
            result = subprocess.run(
                ["netsh", "wlan", "show", "interfaces"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            for line in result.stdout.split('\n'):
                if "SSID" in line and ":" in line:
                    ssid = line.split(":")[-1].strip()
                    if ssid:
                        return ssid
            
            # Fallback: get IP and classify by subnet
            for interface, addrs in psutil.net_if_addrs().items():
                for addr in addrs:
                    if addr.family == socket.AF_INET and not addr.address.startswith("127."):
                        ip = ipaddress.ip_address(addr.address)
                        # Return first 3 octets as network identifier
                        return str(ip).rpartition(".")[0]
            
            return None
            
        except Exception:
            return None


def should_launch_app(conditions: Optional[Dict[str, str]], dry_run: bool = False) -> bool:
    """
    Determine if an app should launch based on conditions.
    
    Args:
        conditions: Conditions dictionary
        dry_run: If True, log decision but don't enforce
        
    Returns:
        True if app should launch
    """
    result = ConditionEvaluator.evaluate(conditions)
    
    if dry_run:
        if not result and conditions:
            print(f"  ℹ️  Skipping due to conditions: {conditions}")
        return True  # Always show in dry run
    
    return result

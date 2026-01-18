"""
Startup metrics tracking and history
"""
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional


class Metrics:
    """Represents startup execution metrics"""
    
    def __init__(self, profile: Optional[str] = None):
        self.start_time = datetime.now()
        self.profile = profile
        self.phase_times: Dict[str, float] = {}
        self.results: Dict[str, bool] = {}
        self.errors: List[str] = []
        self.retry_counts: Dict[str, int] = {}
    
    def record_phase(self, phase: str, duration: float, success: bool):
        """Record phase execution"""
        self.phase_times[phase] = duration
        self.results[phase] = success
    
    def add_error(self, error: str):
        """Add an error"""
        self.errors.append(error)
    
    def set_retry_count(self, app_name: str, count: int):
        """Set retry count for an app"""
        self.retry_counts[app_name] = count
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "timestamp": self.start_time.isoformat(),
            "profile": self.profile,
            "duration_seconds": (datetime.now() - self.start_time).total_seconds(),
            "phases": {
                "phase1": {
                    "duration": self.phase_times.get("phase1", 0),
                    "success": self.results.get("phase1", False)
                },
                "phase2": {
                    "duration": self.phase_times.get("phase2", 0),
                    "success": self.results.get("phase2", False)
                },
                "phase3": {
                    "duration": self.phase_times.get("phase3", 0),
                    "success": self.results.get("phase3", False)
                }
            },
            "errors": self.errors,
            "retries": self.retry_counts,
            "overall_success": all(self.results.values())
        }
    
    def save(self, metrics_dir: str = "logs"):
        """Save metrics to file"""
        metrics_path = Path(metrics_dir) / "metrics.jsonl"
        
        # Ensure directory exists
        metrics_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Append to metrics file (newline-delimited JSON)
        with open(metrics_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(self.to_dict()) + '\n')
        
        return str(metrics_path)


class MetricsTracker:
    """Manages metrics tracking and history"""
    
    def __init__(self, metrics_dir: str = "logs"):
        self.metrics_dir = Path(metrics_dir)
        self.current: Optional[Metrics] = None
    
    def start(self, profile: Optional[str] = None) -> Metrics:
        """Start tracking a new session"""
        self.current = Metrics(profile)
        return self.current
    
    def get_history(self, limit: int = 10) -> List[Dict]:
        """
        Get metrics history.
        
        Args:
            limit: Maximum number of records to retrieve (most recent first)
            
        Returns:
            List of metric dictionaries
        """
        metrics_path = self.metrics_dir / "metrics.jsonl"
        
        if not metrics_path.exists():
            return []
        
        history = []
        with open(metrics_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    try:
                        history.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
        
        # Return most recent first
        return history[-limit:][::-1]
    
    def get_summary(self) -> Dict:
        """Get summary statistics of all recorded runs"""
        history = self.get_history(limit=1000)  # Get all recent history
        
        if not history:
            return {
                "total_runs": 0,
                "success_rate": 0,
                "avg_duration": 0,
                "last_run": None
            }
        
        total_runs = len(history)
        successful_runs = sum(1 for h in history if h.get("overall_success", False))
        total_duration = sum(h.get("duration_seconds", 0) for h in history)
        avg_duration = total_duration / total_runs if total_runs > 0 else 0
        
        return {
            "total_runs": total_runs,
            "success_rate": (successful_runs / total_runs * 100) if total_runs > 0 else 0,
            "avg_duration": avg_duration,
            "last_run": history[0]["timestamp"] if history else None
        }
    
    def format_history(self, limit: int = 10) -> str:
        """Format metrics history for display"""
        history = self.get_history(limit)
        
        if not history:
            return "No metrics recorded yet."
        
        lines = []
        lines.append("=" * 80)
        lines.append("Startup History")
        lines.append("=" * 80)
        
        for i, m in enumerate(history[:limit], 1):
            timestamp = m["timestamp"][:19]  # Remove microseconds
            duration = f"{m['duration_seconds']:.1f}s"
            success = "✓" if m.get("overall_success", False) else "✗"
            profile = f" ({m.get('profile', 'default')})" if m.get('profile') else ""
            
            lines.append(f"{i}. {timestamp}{profile} | {duration} | {success}")
            
            if m.get("errors"):
                for error in m["errors"]:
                    lines.append(f"   ✗ {error}")
        
        lines.append("=" * 80)
        
        return "\n".join(lines)
    
    def format_summary(self) -> str:
        """Format summary statistics for display"""
        summary = self.get_summary()
        
        lines = []
        lines.append("=" * 40)
        lines.append("Summary Statistics")
        lines.append("=" * 40)
        lines.append(f"Total Runs: {summary['total_runs']}")
        lines.append(f"Success Rate: {summary['success_rate']:.1f}%")
        lines.append(f"Avg Duration: {summary['avg_duration']:.1f}s")
        if summary['last_run']:
            lines.append(f"Last Run: {summary['last_run'][:19]}")
        lines.append("=" * 40)
        
        return "\n".join(lines)


def format_ascii_chart(history: List[Dict]) -> str:
    """Create simple ASCII chart of startup durations"""
    if not history:
        return "No data for chart."
    
    lines = []
    durations = [h.get("duration_seconds", 0) for h in history]
    max_duration = max(durations) if durations else 1
    
    lines.append("\nStartup Duration Trend:")
    lines.append("=" * 60)
    
    for i, (h, duration) in enumerate(zip(history, durations)):
        bar_length = int((duration / max_duration) * 40)
        bar = "█" * bar_length
        lines.append(f"{h['timestamp'][:10]} | {duration:5.1f}s |{bar}")
    
    lines.append("=" * 60)
    
    return "\n".join(lines)

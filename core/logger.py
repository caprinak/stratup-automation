"""
Logging configuration with rotating file handler
"""
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from datetime import datetime
import sys


def setup_logger(
    name: str = "startup",
    log_dir: str = "logs",
    level: str = "INFO"
) -> logging.Logger:
    """
    Set up a logger with both console and file output.
    
    Returns:
        Configured logger instance
    """
    # Create logs directory
    log_path = Path(log_dir)
    log_path.mkdir(exist_ok=True)
    
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    
    # Prevent duplicate handlers
    if logger.handlers:
        return logger
    
    # Formatter
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # Console handler (colored output)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler (rotating)
    log_file = log_path / f"startup_{datetime.now().strftime('%Y-%m-%d')}.log"
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=5 * 1024 * 1024,  # 5 MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    return logger


def get_logger(name: str = "startup") -> logging.Logger:
    """Get existing logger or create new one."""
    return logging.getLogger(name)

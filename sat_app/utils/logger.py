"""
Logging utility module for the SAT Question Bank application.
Configures application-wide logging for debugging and error reporting.
"""
import os
import logging
import sys
from datetime import datetime


class SafeUnicodeFormatter(logging.Formatter):
    """Custom formatter that safely handles Unicode characters."""
    
    def format(self, record):
        """Format the log record, ensuring Unicode safety."""
        try:
            # Get the formatted message
            formatted = super().format(record)
            # Ensure it can be encoded safely
            formatted.encode('utf-8', errors='replace')
            return formatted
        except (UnicodeEncodeError, UnicodeDecodeError):
            # If there's an encoding issue, create a safe version
            try:
                safe_msg = str(record.getMessage()).encode('utf-8', errors='replace').decode('utf-8')
                record.msg = safe_msg
                return super().format(record)
            except Exception:
                # Last resort: return a basic safe message
                return f"{record.levelname}: [Unicode encoding error in log message]"


def setup_logger(log_level=logging.INFO, log_to_file=True):
    """
    Set up application-wide logging with Unicode support.
    
    Args:
        log_level: The logging level (default: INFO)
        log_to_file: Whether to log to a file (default: True)
    
    Returns:
        The configured logger instance
    """
    # Create logs directory if it doesn't exist
    if log_to_file and not os.path.exists('logs'):
        os.makedirs('logs')
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Clear existing handlers to avoid duplicates
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Set log format with Unicode safety
    formatter = SafeUnicodeFormatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Add console handler with UTF-8 encoding
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    # Ensure console output uses UTF-8 encoding
    if hasattr(console_handler.stream, 'reconfigure'):
        try:
            console_handler.stream.reconfigure(encoding='utf-8', errors='replace')
        except (AttributeError, OSError):
            pass  # Fall back to default behavior if reconfigure is not available
    root_logger.addHandler(console_handler)
    
    # Add file handler if enabled with UTF-8 encoding
    if log_to_file:
        log_file = f'logs/sat_app_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
        file_handler = logging.FileHandler(log_file, encoding='utf-8', errors='replace')
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    
    # Return the configured logger
    return root_logger


def get_logger(name):
    """
    Get a logger for a specific module.
    
    Args:
        name: The name of the module (typically __name__)
    
    Returns:
        A logger instance
    """
    return logging.getLogger(name)
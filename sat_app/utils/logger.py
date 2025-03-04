"""
Logging utility module for the SAT Question Bank application.
Configures application-wide logging for debugging and error reporting.
"""
import os
import logging
import sys
from datetime import datetime


def setup_logger(log_level=logging.INFO, log_to_file=True):
    """
    Set up application-wide logging.
    
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
    
    # Set log format
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Add console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # Add file handler if enabled
    if log_to_file:
        log_file = f'logs/sat_app_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
        file_handler = logging.FileHandler(log_file)
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
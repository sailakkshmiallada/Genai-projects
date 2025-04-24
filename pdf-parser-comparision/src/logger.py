"""
Logger utility module for PDF Playground.

This module provides a centralized logging configuration for the entire application.
It sets up logging with both file and console handlers, with different log levels
and formatting for different environments.
"""

import logging
import os
from datetime import datetime

def setup_logger(name: str) -> logging.Logger:
    """
    Set up and configure a logger instance for a given module.

    Args:
        name (str): Name of the module requesting the logger

    Returns:
        logging.Logger: Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Prevent adding handlers multiple times
    if logger.hasHandlers():
        return logger

    logger.setLevel(logging.DEBUG)

    # Create logs directory if it doesn't exist
    logs_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
    os.makedirs(logs_dir, exist_ok=True)

    # File handler - for detailed logging
    log_file = os.path.join(logs_dir, f'pdf_playground_{datetime.now().strftime("%Y%m%d")}.log')
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(file_formatter)

    # Console handler - for basic logging
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter('%(levelname)s - %(message)s')
    console_handler.setFormatter(console_formatter)

    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger
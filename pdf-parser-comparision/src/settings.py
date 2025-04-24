"""
Application Settings Module

This module manages global application settings through environment variables.
It provides configuration for debug mode and formula processing features.
"""

import os
from .logger import setup_logger

# Initialize module logger
logger = setup_logger(__name__)

def get_boolean_env(key: str, default: bool = True) -> bool:
    """
    Get a boolean value from an environment variable.
    
    Args:
        key (str): Environment variable name
        default (bool): Default value if not set
        
    Returns:
        bool: The parsed boolean value
    """
    value = os.environ.get(key, str(default)).lower()
    result = value in ("true", "1", "yes", "on")
    logger.debug(f"Config {key}={result} (from env={value})")
    return result

# Application settings
ENABLE_DEBUG_MODE = get_boolean_env("ENABLE_DEBUG_MODE", True)
ENABLE_FORMULA = get_boolean_env("ENABLE_FORMULA", True)

# Log initial configuration
logger.info("Application settings loaded:")
logger.info(f"Debug mode: {'enabled' if ENABLE_DEBUG_MODE else 'disabled'}")
logger.info(f"Formula processing: {'enabled' if ENABLE_FORMULA else 'disabled'}")

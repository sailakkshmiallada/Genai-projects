import logging
import os
from pathlib import Path
import sys
import logfire

# Track if logging has been configured
_logging_configured = False

class Logger:
    """
    Centralized logging utility that uses logfire for enhanced logging.
    """
    
    def __init__(self, name=None):
        """
        Initialize the logger with the given name.
        
        Args:
            name: The name of the logger, usually __name__ of the calling module
        """
        global _logging_configured
        
        # Configure logfire once across all instances
        if not _logging_configured:
            logfire.configure()
            
            # Set up the logging handler
            handler = logfire.LogfireLoggingHandler()
            
            # Reset root logger handlers to avoid duplicates
            root_logger = logging.getLogger()
            for handler in root_logger.handlers[:]:
                root_logger.removeHandler(handler)
            
            # Configure basic logging - use ONLY the logfire handler
            logging.basicConfig(
                level=logging.INFO,
                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                handlers=[handler]
            )
            
            _logging_configured = True
        
        # Create a logger with the given name
        self.logger = logging.getLogger(name or __name__)
    
    def debug(self, msg, *args, **kwargs):
        """Log a debug message."""
        self.logger.debug(msg, *args, **kwargs)
    
    def info(self, msg, *args, **kwargs):
        """Log an info message."""
        self.logger.info(msg, *args, **kwargs)
    
    def warning(self, msg, *args, **kwargs):
        """Log a warning message."""
        self.logger.warning(msg, *args, **kwargs)
    
    def error(self, msg, *args, **kwargs):
        """Log an error message."""
        self.logger.error(msg, *args, **kwargs)
    
    def critical(self, msg, *args, **kwargs):
        """Log a critical message."""
        self.logger.critical(msg, *args, **kwargs)
    
    def exception(self, msg, *args, exc_info=True, **kwargs):
        """Log an exception with traceback."""
        self.logger.exception(msg, *args, exc_info=exc_info, **kwargs)


# Singleton instance
_logger_instances = {}

def get_logger(name=None):
    """
    Get a configured logger instance.
    
    Args:
        name: The name of the logger
        
    Returns:
        Logger: A configured logger instance
    """
    if name not in _logger_instances:
        _logger_instances[name] = Logger(name)
    return _logger_instances[name] 
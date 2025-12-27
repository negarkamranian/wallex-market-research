import logging
import sys
from pythonjsonlogger import jsonlogger


def setup_logging() -> None:
    """Configure application logging with JSON format."""
    
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.INFO)
    
    formatter = jsonlogger.JsonFormatter(
        "%(asctime)s %(name)s %(levelname)s %(message)s",
        timestamp=True
    )
    handler.setFormatter(formatter)
    
    logger.addHandler(handler)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance for a specific module.
    
    Args:
        name: Module name for the logger
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)

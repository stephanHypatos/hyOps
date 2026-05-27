"""
Logging configuration
"""

import logging
import sys
from pathlib import Path
from app.consts.settings import LOGGING_CONFIG


def setup_logger(name: str = "ap_onboarding") -> logging.Logger:
    """
    Setup and configure logger

    Args:
        name: Logger name

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)

    # Only configure if not already configured
    if not logger.handlers:
        logger.setLevel(LOGGING_CONFIG.get("log_level", "INFO"))

        # Create formatters
        formatter = logging.Formatter(
            LOGGING_CONFIG.get("log_format", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        )

        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        # File handler (if log file path is configured)
        log_file = LOGGING_CONFIG.get("log_file")
        if log_file:
            log_file_path = Path(log_file)
            log_file_path.parent.mkdir(parents=True, exist_ok=True)

            file_handler = logging.FileHandler(log_file_path)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

    return logger


# Create default logger
logger = setup_logger()

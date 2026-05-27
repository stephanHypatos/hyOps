"""
Application Configuration Settings
"""

import os
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Logging configuration
LOGGING_CONFIG = {
    "log_level": "INFO",
    "log_file": BASE_DIR / "logs" / "app.log",
    "log_format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
}


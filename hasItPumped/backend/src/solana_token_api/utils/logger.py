"""
Logging configuration for the application.
"""

import json
import logging
import os
import sys
from datetime import datetime, UTC

from logging.handlers import RotatingFileHandler
from pathlib import Path

# Create logs directory if it doesn't exist
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)


class JsonFormatter(logging.Formatter):
    """
    Custom formatter to output logs in JSON format
    """

    def format(self, record):
        log_record = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
            "location": f"{record.pathname}:{record.lineno}",
        }

        # Add exception info if available
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)

        # Add extra attributes from record
        for key, value in record.__dict__.items():
            if key not in [
                "args",
                "exc_info",
                "exc_text",
                "levelname",
                "levelno",
                "lineno",
                "message",
                "module",
                "msecs",
                "msg",
                "name",
                "pathname",
                "process",
                "processName",
                "relativeCreated",
                "stack_info",
                "thread",
                "threadName",
            ]:
                log_record[key] = value

        return json.dumps(log_record)


def setup_logger(name, level=None):
    """
    Set up a logger with file and console handlers.

    Args:
        name: Logger name
        level: Logging level (defaults to environment variable or INFO)

    Returns:
        Configured logger instance
    """
    # Determine log level
    if level is None:
        level_name = os.getenv("LOG_LEVEL", "INFO").upper()
        level = getattr(logging, level_name, logging.INFO)

    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Remove existing handlers to avoid duplicates
    if logger.handlers:
        logger.handlers.clear()

    # Create file handler with rotation
    file_path = log_dir / f"{name.replace('.', '_')}.log"
    file_handler = RotatingFileHandler(
        file_path, maxBytes=10 * 1024 * 1024, backupCount=5  # 10 MB
    )
    file_handler.setFormatter(JsonFormatter())

    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_format = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    console_handler.setFormatter(logging.Formatter(console_format))

    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger

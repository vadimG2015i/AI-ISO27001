"""Structured logging setup for ISO 27001 Assistant."""

import logging
import sys

from iso_assistant.config import settings


def get_logger(name: str) -> logging.Logger:
    """Configures and returns standard logger with consistent formatting."""
    logger = logging.getLogger(name)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)-7s | %(name)s:%(funcName)s:%(lineno)d - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    level = logging.DEBUG if settings.debug else getattr(logging, settings.log_level.upper(), logging.INFO)
    logger.setLevel(level)
    return logger


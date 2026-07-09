"""
LexOrch-KG — Loguru Logging Configuration
Structured logging with rotation, retention, and JSON output for production.
"""

import sys
from loguru import logger

from app.core.config import settings


def configure_logging() -> None:
    """
    Configure Loguru with appropriate sinks for development and production.
    
    - Development: colored console output
    - Production: JSON-formatted file logs with rotation
    """
    # Remove default handler
    logger.remove()

    # Reconfigure sys.stdout encoding to handle UTF-8 symbols in Windows consoles
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass

    # ── Console sink ────────────────────────────────────────────────────────
    log_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>"
    )
    logger.add(
        sys.stdout,
        format=log_format,
        level="DEBUG" if settings.debug else "INFO",
        colorize=True,
    )

    # ── File sink (rotating) ─────────────────────────────────────────────────
    logger.add(
        "logs/lexorch_{time:YYYY-MM-DD}.log",
        rotation="00:00",          # New file at midnight
        retention="30 days",       # Keep 30 days of logs
        compression="gz",          # Compress old logs
        level="INFO",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}",
        enqueue=True,              # Thread-safe async logging
    )

    # ── Error-only file ──────────────────────────────────────────────────────
    logger.add(
        "logs/errors_{time:YYYY-MM-DD}.log",
        rotation="1 week",
        retention="90 days",
        compression="gz",
        level="ERROR",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}\n{exception}",
        enqueue=True,
        backtrace=True,
        diagnose=True,
    )

    logger.info(
        f"Logging configured | env={settings.environment} debug={settings.debug}"
    )

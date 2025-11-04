"""
Logging configuration for MMDVMHost state machine.

This module sets up structured logging for the application with proper
formatting, rotation, and output to both file and console.

Logging is configured centrally and used throughout all modules.
"""

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

from mmdvm_state_machine.config import LoggingConfig


def setup_logging(config: LoggingConfig) -> logging.Logger:
    """
    Configure application logging based on configuration.

    This sets up:
    - Root logger with configured level
    - Console handler (stdout) for all logs
    - Rotating file handler (if file path specified)
    - Consistent formatting across all handlers

    Args:
        config: Logging configuration

    Returns:
        Configured root logger

    Raises:
        OSError: If log file cannot be created or written
    """
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(config.level)

    # Remove existing handlers to avoid duplicates
    root_logger.handlers.clear()

    # Create formatter
    formatter = logging.Formatter(config.format)

    # Console handler (stdout)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(config.level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # File handler (if configured)
    if config.file:
        log_file_path = Path(config.file)

        # Create directory if it doesn't exist
        log_file_path.parent.mkdir(parents=True, exist_ok=True)

        if config.rotation.enabled:
            # Rotating file handler
            file_handler = RotatingFileHandler(
                filename=config.file,
                maxBytes=config.rotation.max_bytes,
                backupCount=config.rotation.backup_count,
                encoding="utf-8",
            )
        else:
            # Standard file handler
            file_handler = logging.FileHandler(
                filename=config.file,
                encoding="utf-8",
            )

        file_handler.setLevel(config.level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    # Log initial setup message
    root_logger.info(
        f"Logging initialized: level={config.level}, file={config.file}"
    )

    return root_logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a specific module.

    This should be called at the module level:
        logger = get_logger(__name__)

    Args:
        name: Logger name (typically __name__)

    Returns:
        Logger instance
    """
    return logging.getLogger(name)


class LoggerAdapter(logging.LoggerAdapter):
    """
    Custom logger adapter that adds contextual information.

    This can be used to add consistent context (like request IDs, user IDs, etc.)
    to all log messages from a particular context.

    Example:
        logger = get_logger(__name__)
        context_logger = LoggerAdapter(logger, {"request_id": "12345"})
        context_logger.info("Processing request")
        # Output: ... - Processing request [request_id=12345]
    """

    def process(self, msg: str, kwargs: dict) -> tuple[str, dict]:
        """
        Process the logging message and keyword arguments.

        Args:
            msg: Log message
            kwargs: Keyword arguments

        Returns:
            Tuple of (processed message, kwargs)
        """
        # Add extra context to message
        if self.extra:
            extra_str = " ".join(f"{k}={v}" for k, v in self.extra.items())
            msg = f"{msg} [{extra_str}]"
        return msg, kwargs


def log_exception(
    logger: logging.Logger,
    message: str,
    exc_info: bool = True,
) -> None:
    """
    Log an exception with consistent formatting.

    This is a convenience function for logging exceptions with full traceback.

    Args:
        logger: Logger instance to use
        message: Context message to log
        exc_info: Whether to include exception info (default True)

    Example:
        try:
            risky_operation()
        except Exception as e:
            log_exception(logger, "Failed to perform risky operation")
    """
    logger.error(message, exc_info=exc_info)


def log_security_event(
    logger: logging.Logger,
    event_type: str,
    details: str,
    severity: str = "WARNING",
) -> None:
    """
    Log a security-related event with consistent formatting.

    Security events are logged at WARNING or ERROR level and include
    a consistent prefix for easy filtering.

    Args:
        logger: Logger instance to use
        event_type: Type of security event (e.g., "AUTH_FAILURE", "RATE_LIMIT")
        details: Detailed description of the event
        severity: Log severity (WARNING or ERROR)

    Example:
        log_security_event(
            logger,
            "AUTH_FAILURE",
            "Invalid API key from 192.168.1.100",
            "ERROR"
        )
    """
    message = f"SECURITY [{event_type}]: {details}"
    log_level = getattr(logging, severity.upper(), logging.WARNING)
    logger.log(log_level, message)


def log_performance_metric(
    logger: logging.Logger,
    metric_name: str,
    value: float,
    unit: str = "",
) -> None:
    """
    Log a performance metric.

    Performance metrics are logged at DEBUG level with a consistent format
    that makes them easy to parse and aggregate.

    Args:
        logger: Logger instance to use
        metric_name: Name of the metric
        value: Metric value
        unit: Unit of measurement (optional)

    Example:
        log_performance_metric(logger, "qso_parse_time", 0.0023, "seconds")
    """
    unit_str = f" {unit}" if unit else ""
    logger.debug(f"METRIC [{metric_name}]: {value}{unit_str}")

"""
Configuration management for MMDVMHost state machine.

This module handles loading and validation of configuration from YAML files,
with support for environment variable overrides and sensible defaults.

Configuration is loaded using Pydantic settings for type safety and validation.
"""

import os
from pathlib import Path
from typing import List, Dict, Optional

import yaml
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class LogMonitoringConfig(BaseSettings):
    """
    Configuration for log file monitoring.
    """

    log_path_pattern: str = Field(
        "/var/log/mmdvm/MMDVM-*.log",
        description="Glob pattern for MMDVM log files",
    )
    log_directory: str = Field(
        "/var/log/mmdvm", description="Directory containing log files"
    )
    rotation_check_interval: int = Field(
        60, description="Interval to check for log rotation (seconds)"
    )
    read_buffer_size: int = Field(8192, description="Read buffer size in bytes")

    @field_validator("log_directory")
    @classmethod
    def validate_log_directory(cls, v: str) -> str:
        """Validate that log directory path is absolute."""
        path = Path(v)
        if not path.is_absolute():
            raise ValueError(f"log_directory must be an absolute path, got: {v}")
        return v


class StateMachineConfig(BaseSettings):
    """
    Configuration for the state machine.
    """

    qso_history_size: int = Field(
        100, description="Number of QSOs to retain in history"
    )
    qso_timeout_seconds: int = Field(
        30, description="QSO timeout (no activity)"
    )
    supported_modes: List[str] = Field(
        default_factory=lambda: ["DSTAR", "DMR", "YSF", "P25", "NXDN", "POCSAG", "FM", "IDLE"],
        description="Supported operating modes",
    )

    @field_validator("qso_history_size")
    @classmethod
    def validate_history_size(cls, v: int) -> int:
        """Validate QSO history size is reasonable."""
        if v < 1 or v > 10000:
            raise ValueError("qso_history_size must be between 1 and 10000")
        return v

    @field_validator("qso_timeout_seconds")
    @classmethod
    def validate_timeout(cls, v: int) -> int:
        """Validate timeout is reasonable."""
        if v < 1 or v > 3600:
            raise ValueError("qso_timeout_seconds must be between 1 and 3600")
        return v


class RateLimitConfig(BaseSettings):
    """
    Rate limiting configuration.
    """

    enabled: bool = Field(False, description="Enable rate limiting")
    requests_per_minute: int = Field(60, description="Maximum requests per minute")


class APIConfig(BaseSettings):
    """
    Configuration for REST API server.
    """

    host: str = Field("0.0.0.0", description="API server host")
    port: int = Field(8080, description="API server port")
    enable_cors: bool = Field(True, description="Enable CORS")
    cors_origins: List[str] = Field(
        default_factory=lambda: [
            "http://localhost",
            "http://localhost:3000",
            "http://localhost:8080",
        ],
        description="Allowed CORS origins",
    )
    require_auth: bool = Field(False, description="Require API authentication")
    api_keys: Dict[str, str] = Field(
        default_factory=dict, description="API keys (name: key)"
    )
    rate_limit: RateLimitConfig = Field(
        default_factory=RateLimitConfig, description="Rate limiting config"
    )

    @field_validator("port")
    @classmethod
    def validate_port(cls, v: int) -> int:
        """Validate port is in valid range."""
        if v < 1 or v > 65535:
            raise ValueError("port must be between 1 and 65535")
        return v


class WebSocketConfig(BaseSettings):
    """
    Configuration for WebSocket server.
    """

    max_connections: int = Field(50, description="Maximum concurrent connections")
    ping_interval: int = Field(30, description="Ping interval (seconds)")
    timeout: int = Field(300, description="Connection timeout (seconds)")

    @field_validator("max_connections")
    @classmethod
    def validate_max_connections(cls, v: int) -> int:
        """Validate max connections is reasonable."""
        if v < 1 or v > 1000:
            raise ValueError("max_connections must be between 1 and 1000")
        return v


class LogRotationConfig(BaseSettings):
    """
    Application log rotation configuration.
    """

    enabled: bool = Field(True, description="Enable log rotation")
    max_bytes: int = Field(10485760, description="Max log file size (bytes)")
    backup_count: int = Field(5, description="Number of backup files to keep")


class LoggingConfig(BaseSettings):
    """
    Configuration for application logging.
    """

    level: str = Field("INFO", description="Log level")
    file: Optional[str] = Field(
        "/var/log/mmdvm-state-machine/app.log", description="Log file path"
    )
    format: str = Field(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="Log format string",
    )
    rotation: LogRotationConfig = Field(
        default_factory=LogRotationConfig, description="Log rotation config"
    )

    @field_validator("level")
    @classmethod
    def validate_level(cls, v: str) -> str:
        """Validate log level is valid."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        v_upper = v.upper()
        if v_upper not in valid_levels:
            raise ValueError(f"level must be one of: {', '.join(valid_levels)}")
        return v_upper


class PerformanceConfig(BaseSettings):
    """
    Performance tuning configuration.
    """

    use_uvloop: bool = Field(True, description="Use uvloop for async (Linux only)")
    workers: int = Field(1, description="Number of worker processes")
    enable_metrics: bool = Field(False, description="Enable Prometheus metrics")

    @field_validator("workers")
    @classmethod
    def validate_workers(cls, v: int) -> int:
        """Validate worker count is reasonable."""
        if v < 1 or v > 16:
            raise ValueError("workers must be between 1 and 16")
        return v


class Config(BaseSettings):
    """
    Main configuration object.

    This aggregates all configuration sections and provides loading from YAML files.
    """

    model_config = SettingsConfigDict(
        env_prefix="MMDVM_",
        env_nested_delimiter="__",
        case_sensitive=False,
    )

    log_monitoring: LogMonitoringConfig = Field(
        default_factory=LogMonitoringConfig
    )
    state_machine: StateMachineConfig = Field(
        default_factory=StateMachineConfig
    )
    api: APIConfig = Field(default_factory=APIConfig)
    websocket: WebSocketConfig = Field(default_factory=WebSocketConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    performance: PerformanceConfig = Field(default_factory=PerformanceConfig)

    @classmethod
    def from_yaml(cls, yaml_path: str) -> "Config":
        """
        Load configuration from a YAML file.

        This method reads the YAML file, parses it, and constructs a validated
        Config object. Environment variables can still override YAML values.

        Args:
            yaml_path: Path to YAML configuration file

        Returns:
            Validated Config object

        Raises:
            FileNotFoundError: If YAML file doesn't exist
            yaml.YAMLError: If YAML is malformed
            ValueError: If configuration validation fails
        """
        yaml_file = Path(yaml_path)
        if not yaml_file.exists():
            raise FileNotFoundError(f"Configuration file not found: {yaml_path}")

        with yaml_file.open("r") as f:
            config_dict = yaml.safe_load(f)

        if config_dict is None:
            config_dict = {}

        # Create nested config objects
        return cls(
            log_monitoring=LogMonitoringConfig(**config_dict.get("log_monitoring", {})),
            state_machine=StateMachineConfig(**config_dict.get("state_machine", {})),
            api=APIConfig(**config_dict.get("api", {})),
            websocket=WebSocketConfig(**config_dict.get("websocket", {})),
            logging=LoggingConfig(**config_dict.get("logging", {})),
            performance=PerformanceConfig(**config_dict.get("performance", {})),
        )

    @classmethod
    def get_default_config_path(cls) -> Path:
        """
        Get the default configuration file path.

        Searches in order:
        1. MMDVM_CONFIG environment variable
        2. ./config.yaml (current directory)
        3. ~/.config/mmdvm-state-machine/config.yaml
        4. /etc/mmdvm-state-machine/config.yaml

        Returns:
            Path to configuration file

        Raises:
            FileNotFoundError: If no configuration file found
        """
        # Check environment variable
        env_path = os.environ.get("MMDVM_CONFIG")
        if env_path:
            path = Path(env_path)
            if path.exists():
                return path

        # Check standard locations
        search_paths = [
            Path("config.yaml"),
            Path.home() / ".config" / "mmdvm-state-machine" / "config.yaml",
            Path("/etc/mmdvm-state-machine/config.yaml"),
        ]

        for path in search_paths:
            if path.exists():
                return path

        raise FileNotFoundError(
            "No configuration file found. Please create config.yaml or set MMDVM_CONFIG"
        )

    def validate_runtime(self) -> None:
        """
        Perform runtime validation checks.

        This validates that paths exist, permissions are correct, etc.
        Called after configuration is loaded but before starting services.

        Raises:
            ValueError: If runtime validation fails
        """
        # Check log directory exists and is readable
        log_dir = Path(self.log_monitoring.log_directory)
        if not log_dir.exists():
            raise ValueError(
                f"Log directory does not exist: {self.log_monitoring.log_directory}"
            )
        if not os.access(log_dir, os.R_OK):
            raise ValueError(
                f"Log directory is not readable: {self.log_monitoring.log_directory}"
            )

        # Check application log directory is writable (if specified)
        if self.logging.file:
            app_log_dir = Path(self.logging.file).parent
            if not app_log_dir.exists():
                try:
                    app_log_dir.mkdir(parents=True, exist_ok=True)
                except OSError as e:
                    raise ValueError(
                        f"Cannot create log directory {app_log_dir}: {e}"
                    )
            if not os.access(app_log_dir, os.W_OK):
                raise ValueError(
                    f"Log directory is not writable: {app_log_dir}"
                )


def load_config(config_path: Optional[str] = None) -> Config:
    """
    Load configuration with automatic path detection.

    This is the primary entry point for configuration loading.

    Args:
        config_path: Optional explicit path to config file

    Returns:
        Validated Config object

    Raises:
        FileNotFoundError: If configuration file not found
        ValueError: If configuration is invalid
    """
    if config_path:
        config = Config.from_yaml(config_path)
    else:
        try:
            default_path = Config.get_default_config_path()
            config = Config.from_yaml(str(default_path))
        except FileNotFoundError:
            # Fall back to default config if no file found
            config = Config()

    # Perform runtime validation
    config.validate_runtime()

    return config

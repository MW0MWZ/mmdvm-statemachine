"""
Unit tests for configuration management.

Tests YAML loading, validation, and environment variable overrides.
"""

import os
import pytest
import tempfile
from pathlib import Path

from mmdvm_state_machine.config import (
    Config,
    LogMonitoringConfig,
    StateMachineConfig,
    APIConfig,
    LoggingConfig,
    load_config,
)


class TestLogMonitoringConfig:
    """Tests for log monitoring configuration."""

    def test_default_values(self):
        """Test default configuration values."""
        config = LogMonitoringConfig()

        assert config.log_path_pattern == "/var/log/mmdvm/MMDVM-*.log"
        assert config.log_directory == "/var/log/mmdvm"
        assert config.rotation_check_interval == 60
        assert config.read_buffer_size == 8192

    def test_absolute_path_validation(self):
        """Test that log_directory must be absolute."""
        with pytest.raises(ValueError, match="must be an absolute path"):
            LogMonitoringConfig(log_directory="relative/path")


class TestStateMachineConfig:
    """Tests for state machine configuration."""

    def test_default_values(self):
        """Test default configuration values."""
        config = StateMachineConfig()

        assert config.qso_history_size == 100
        assert config.qso_timeout_seconds == 30
        assert "DMR" in config.supported_modes
        assert "YSF" in config.supported_modes

    def test_history_size_validation(self):
        """Test QSO history size validation."""
        # Valid range
        config = StateMachineConfig(qso_history_size=50)
        assert config.qso_history_size == 50

        # Too small
        with pytest.raises(ValueError, match="between 1 and 10000"):
            StateMachineConfig(qso_history_size=0)

        # Too large
        with pytest.raises(ValueError, match="between 1 and 10000"):
            StateMachineConfig(qso_history_size=100000)

    def test_timeout_validation(self):
        """Test QSO timeout validation."""
        # Valid
        config = StateMachineConfig(qso_timeout_seconds=60)
        assert config.qso_timeout_seconds == 60

        # Too small
        with pytest.raises(ValueError, match="between 1 and 3600"):
            StateMachineConfig(qso_timeout_seconds=0)

        # Too large
        with pytest.raises(ValueError, match="between 1 and 3600"):
            StateMachineConfig(qso_timeout_seconds=7200)


class TestAPIConfig:
    """Tests for API configuration."""

    def test_default_values(self):
        """Test default API configuration."""
        config = APIConfig()

        assert config.host == "0.0.0.0"
        assert config.port == 8080
        assert config.enable_cors is True
        assert config.require_auth is False

    def test_port_validation(self):
        """Test port number validation."""
        # Valid port
        config = APIConfig(port=3000)
        assert config.port == 3000

        # Invalid - too small
        with pytest.raises(ValueError, match="between 1 and 65535"):
            APIConfig(port=0)

        # Invalid - too large
        with pytest.raises(ValueError, match="between 1 and 65535"):
            APIConfig(port=70000)


class TestLoggingConfig:
    """Tests for logging configuration."""

    def test_default_values(self):
        """Test default logging configuration."""
        config = LoggingConfig()

        assert config.level == "INFO"
        assert config.file == "/var/log/mmdvm-state-machine/app.log"
        assert config.rotation.enabled is True
        assert config.rotation.max_bytes == 10485760  # 10 MB

    def test_log_level_validation(self):
        """Test log level validation."""
        # Valid levels (case insensitive)
        for level in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            config = LoggingConfig(level=level)
            assert config.level == level

            config = LoggingConfig(level=level.lower())
            assert config.level == level

        # Invalid level
        with pytest.raises(ValueError, match="must be one of"):
            LoggingConfig(level="INVALID")


class TestConfigFromYAML:
    """Tests for loading configuration from YAML files."""

    def test_load_minimal_yaml(self):
        """Test loading minimal YAML configuration."""
        yaml_content = """
log_monitoring:
  log_directory: /tmp/mmdvm-test
  log_path_pattern: /tmp/mmdvm-test/*.log

logging:
  level: DEBUG
  file: /tmp/test.log
"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False
        ) as f:
            f.write(yaml_content)
            yaml_path = f.name

        try:
            config = Config.from_yaml(yaml_path)

            assert config.log_monitoring.log_directory == "/tmp/mmdvm-test"
            assert config.logging.level == "DEBUG"
            assert config.logging.file == "/tmp/test.log"
            # Defaults should still work
            assert config.api.port == 8080
        finally:
            os.unlink(yaml_path)

    def test_load_complete_yaml(self):
        """Test loading complete YAML configuration."""
        yaml_content = """
log_monitoring:
  log_directory: /tmp/mmdvm-test
  log_path_pattern: /tmp/mmdvm-test/*.log
  rotation_check_interval: 30

state_machine:
  qso_history_size: 200
  qso_timeout_seconds: 60

api:
  host: 127.0.0.1
  port: 9090
  enable_cors: false

logging:
  level: WARNING
  file: /tmp/app.log
"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False
        ) as f:
            f.write(yaml_content)
            yaml_path = f.name

        try:
            config = Config.from_yaml(yaml_path)

            assert config.log_monitoring.rotation_check_interval == 30
            assert config.state_machine.qso_history_size == 200
            assert config.state_machine.qso_timeout_seconds == 60
            assert config.api.host == "127.0.0.1"
            assert config.api.port == 9090
            assert config.api.enable_cors is False
            assert config.logging.level == "WARNING"
        finally:
            os.unlink(yaml_path)

    def test_load_nonexistent_file(self):
        """Test loading non-existent file raises error."""
        with pytest.raises(FileNotFoundError):
            Config.from_yaml("/nonexistent/path/config.yaml")

    def test_load_empty_yaml(self):
        """Test loading empty YAML uses defaults."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False
        ) as f:
            f.write("")  # Empty file
            yaml_path = f.name

        try:
            config = Config.from_yaml(yaml_path)

            # Should use all defaults
            assert config.api.port == 8080
            assert config.logging.level == "INFO"
        finally:
            os.unlink(yaml_path)


class TestConfigValidation:
    """Tests for runtime configuration validation."""

    def test_validate_runtime_missing_log_directory(self):
        """Test validation fails if log directory doesn't exist."""
        config = Config(
            log_monitoring=LogMonitoringConfig(
                log_directory="/nonexistent/directory"
            ),
            logging=LoggingConfig(file="/tmp/test.log"),
        )

        with pytest.raises(ValueError, match="does not exist"):
            config.validate_runtime()

    def test_validate_runtime_creates_app_log_directory(self):
        """Test validation creates app log directory if needed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "subdir" / "app.log"

            config = Config(
                log_monitoring=LogMonitoringConfig(log_directory=tmpdir),
                logging=LoggingConfig(file=str(log_file)),
            )

            config.validate_runtime()

            # Directory should be created
            assert log_file.parent.exists()


class TestLoadConfig:
    """Tests for the load_config convenience function."""

    def test_load_config_with_explicit_path(self):
        """Test loading config with explicit path."""
        yaml_content = """
logging:
  level: DEBUG
  file: /tmp/explicit-test.log
"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False
        ) as f:
            f.write(yaml_content)
            yaml_path = f.name

        try:
            # Mock the log directory to exist
            with tempfile.TemporaryDirectory() as tmpdir:
                yaml_with_dir = f"""
log_monitoring:
  log_directory: {tmpdir}

logging:
  level: DEBUG
  file: /tmp/explicit-test.log
"""
                with open(yaml_path, "w") as f2:
                    f2.write(yaml_with_dir)

                config = load_config(yaml_path)

                assert config.logging.level == "DEBUG"
        finally:
            if Path(yaml_path).exists():
                os.unlink(yaml_path)

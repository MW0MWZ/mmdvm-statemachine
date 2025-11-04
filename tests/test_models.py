"""
Unit tests for data models.

Tests Pydantic models for validation, serialization, and business logic.
"""

import pytest
from datetime import datetime, timedelta
from uuid import UUID

from mmdvm_state_machine.models import (
    Mode,
    QSOStatus,
    QSO,
    SystemState,
    ModemState,
    Event,
    HealthStatus,
    NetworkStatus,
    ModeStatus,
)


class TestQSOModel:
    """Tests for QSO model."""

    def test_qso_creation_defaults(self):
        """Test QSO creation with minimal parameters."""
        qso = QSO(mode=Mode.DMR)

        assert qso.mode == Mode.DMR
        assert qso.status == QSOStatus.STARTING
        assert isinstance(qso.id, UUID)
        assert isinstance(qso.start_time, datetime)
        assert qso.end_time is None
        assert qso.duration_seconds is None
        assert qso.rf_source is True

    def test_qso_creation_with_all_fields(self):
        """Test QSO creation with all fields populated."""
        start_time = datetime.now()
        qso = QSO(
            mode=Mode.DMR,
            status=QSOStatus.ACTIVE,
            source_callsign="G4KLX",
            destination="TG 235",
            slot=1,
            talk_group=235,
            source_id=12345,
            ber=0.5,
            rssi=-80,
            rf_source=True,
            start_time=start_time,
        )

        assert qso.source_callsign == "G4KLX"
        assert qso.destination == "TG 235"
        assert qso.slot == 1
        assert qso.talk_group == 235
        assert qso.source_id == 12345
        assert qso.ber == 0.5
        assert qso.rssi == -80
        assert qso.start_time == start_time

    def test_qso_complete(self):
        """Test QSO completion calculates duration."""
        qso = QSO(mode=Mode.DMR)
        start_time = qso.start_time

        # Simulate 2.5 second QSO
        end_time = start_time + timedelta(seconds=2.5)
        qso.complete(end_time)

        assert qso.status == QSOStatus.COMPLETED
        assert qso.end_time == end_time
        assert qso.duration_seconds == pytest.approx(2.5, rel=0.01)

    def test_qso_complete_default_time(self):
        """Test QSO completion with default end time (now)."""
        qso = QSO(mode=Mode.DMR)
        qso.complete()

        assert qso.status == QSOStatus.COMPLETED
        assert qso.end_time is not None
        assert qso.duration_seconds is not None
        assert qso.duration_seconds >= 0

    def test_qso_is_active(self):
        """Test is_active method."""
        qso = QSO(mode=Mode.DMR)

        # STARTING should be active
        qso.status = QSOStatus.STARTING
        assert qso.is_active() is True

        # ACTIVE should be active
        qso.status = QSOStatus.ACTIVE
        assert qso.is_active() is True

        # COMPLETED should not be active
        qso.status = QSOStatus.COMPLETED
        assert qso.is_active() is False

        # TIMEOUT should not be active
        qso.status = QSOStatus.TIMEOUT
        assert qso.is_active() is False

    def test_qso_json_serialization(self):
        """Test QSO can be serialized to JSON."""
        qso = QSO(
            mode=Mode.DMR,
            source_callsign="G4KLX",
            talk_group=235,
        )

        json_dict = qso.model_dump()

        assert json_dict["mode"] == "DMR"
        assert json_dict["source_callsign"] == "G4KLX"
        assert json_dict["talk_group"] == 235
        assert "id" in json_dict
        assert "start_time" in json_dict


class TestSystemState:
    """Tests for SystemState model."""

    def test_system_state_defaults(self):
        """Test SystemState creation with defaults."""
        state = SystemState()

        assert state.current_mode == Mode.IDLE
        assert state.modem_state == ModemState.UNKNOWN
        assert len(state.active_qsos) == 0
        assert state.error_count == 0
        assert state.last_error is None
        assert isinstance(state.last_update, datetime)

    def test_add_active_qso(self):
        """Test adding a QSO to active list."""
        state = SystemState()
        qso = QSO(mode=Mode.DMR, source_callsign="G4KLX")

        state.add_active_qso(qso)

        assert len(state.active_qsos) == 1
        assert state.active_qsos[0] == qso

    def test_remove_active_qso(self):
        """Test removing a QSO from active list."""
        state = SystemState()
        qso1 = QSO(mode=Mode.DMR, source_callsign="G4KLX")
        qso2 = QSO(mode=Mode.YSF, source_callsign="M0ABC")

        state.add_active_qso(qso1)
        state.add_active_qso(qso2)

        removed = state.remove_active_qso(qso1.id)

        assert removed == qso1
        assert len(state.active_qsos) == 1
        assert state.active_qsos[0] == qso2

    def test_remove_nonexistent_qso(self):
        """Test removing a QSO that doesn't exist."""
        state = SystemState()
        qso = QSO(mode=Mode.DMR)

        state.add_active_qso(qso)

        # Try to remove non-existent QSO
        from uuid import uuid4

        removed = state.remove_active_qso(uuid4())

        assert removed is None
        assert len(state.active_qsos) == 1

    def test_get_active_qso_by_id(self):
        """Test retrieving a QSO by ID."""
        state = SystemState()
        qso1 = QSO(mode=Mode.DMR, source_callsign="G4KLX")
        qso2 = QSO(mode=Mode.YSF, source_callsign="M0ABC")

        state.add_active_qso(qso1)
        state.add_active_qso(qso2)

        found = state.get_active_qso_by_id(qso2.id)

        assert found == qso2

    def test_record_error(self):
        """Test error recording."""
        state = SystemState()

        state.record_error("Test error message")

        assert state.error_count == 1
        assert state.last_error == "Test error message"
        assert state.last_error_time is not None

        # Record another error
        state.record_error("Second error")

        assert state.error_count == 2
        assert state.last_error == "Second error"


class TestEvent:
    """Tests for Event model."""

    def test_event_creation(self):
        """Test event creation."""
        event = Event(
            event_type="qso_started",
            data={"qso_id": "12345", "mode": "DMR"},
            severity="info",
        )

        assert event.event_type == "qso_started"
        assert event.data["qso_id"] == "12345"
        assert event.severity == "info"
        assert isinstance(event.event_id, UUID)
        assert isinstance(event.timestamp, datetime)

    def test_event_json_serialization(self):
        """Test event can be serialized to JSON."""
        event = Event(
            event_type="mode_changed",
            data={"old_mode": "IDLE", "new_mode": "DMR"},
        )

        json_dict = event.model_dump()

        assert json_dict["event_type"] == "mode_changed"
        assert "event_id" in json_dict
        assert "timestamp" in json_dict
        assert "data" in json_dict


class TestHealthStatus:
    """Tests for HealthStatus model."""

    def test_health_status_creation(self):
        """Test health status creation."""
        health = HealthStatus(
            healthy=True,
            version="1.0.0",
            uptime_seconds=3600.0,
            log_monitor_active=True,
            state_machine_active=True,
            api_server_active=True,
            total_qsos_processed=42,
            active_websocket_connections=3,
        )

        assert health.healthy is True
        assert health.version == "1.0.0"
        assert health.uptime_seconds == 3600.0
        assert health.total_qsos_processed == 42
        assert health.active_websocket_connections == 3

    def test_health_status_with_errors(self):
        """Test health status with error information."""
        health = HealthStatus(
            healthy=False,
            version="1.0.0",
            uptime_seconds=100.0,
            log_monitor_active=False,
            state_machine_active=True,
            api_server_active=True,
            error_count=5,
            last_error="Log monitor crashed",
        )

        assert health.healthy is False
        assert health.error_count == 5
        assert health.last_error == "Log monitor crashed"


class TestEnums:
    """Tests for enum types."""

    def test_mode_enum_values(self):
        """Test Mode enum has expected values."""
        assert Mode.DMR.value == "DMR"
        assert Mode.DSTAR.value == "DSTAR"
        assert Mode.YSF.value == "YSF"
        assert Mode.P25.value == "P25"
        assert Mode.NXDN.value == "NXDN"
        assert Mode.POCSAG.value == "POCSAG"
        assert Mode.FM.value == "FM"
        assert Mode.IDLE.value == "IDLE"

    def test_qso_status_enum_values(self):
        """Test QSOStatus enum has expected values."""
        assert QSOStatus.STARTING.value == "STARTING"
        assert QSOStatus.ACTIVE.value == "ACTIVE"
        assert QSOStatus.ENDING.value == "ENDING"
        assert QSOStatus.COMPLETED.value == "COMPLETED"
        assert QSOStatus.TIMEOUT.value == "TIMEOUT"
        assert QSOStatus.ERROR.value == "ERROR"

    def test_modem_state_enum_values(self):
        """Test ModemState enum has expected values."""
        assert ModemState.IDLE.value == "IDLE"
        assert ModemState.RX.value == "RX"
        assert ModemState.TX.value == "TX"
        assert ModemState.ERROR.value == "ERROR"
        assert ModemState.UNKNOWN.value == "UNKNOWN"

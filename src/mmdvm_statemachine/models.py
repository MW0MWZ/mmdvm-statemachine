"""
Data models for MMDVMHost state machine.

This module defines all core data structures used throughout the application,
including QSO records, system state, and configuration models.

All models use Pydantic for validation and serialization, ensuring type safety
and easy JSON conversion for the REST API.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any, List
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, ConfigDict


class Mode(str, Enum):
    """
    Operating modes supported by MMDVMHost.

    These represent the different digital voice and data modes that
    MMDVMHost can handle.
    """

    DSTAR = "DSTAR"
    DMR = "DMR"
    YSF = "YSF"
    P25 = "P25"
    NXDN = "NXDN"
    POCSAG = "POCSAG"
    FM = "FM"
    IDLE = "IDLE"


class QSOStatus(str, Enum):
    """
    QSO (contact) status states.

    Tracks the lifecycle of a radio contact from initiation to completion.
    """

    STARTING = "STARTING"  # QSO initiated, header received
    ACTIVE = "ACTIVE"  # Voice/data transmission in progress
    ENDING = "ENDING"  # End sequence received
    COMPLETED = "COMPLETED"  # QSO fully completed
    TIMEOUT = "TIMEOUT"  # QSO timed out (no activity)
    ERROR = "ERROR"  # QSO ended with error


class ModemState(str, Enum):
    """
    Modem hardware state.

    Represents the physical modem's operational status.
    """

    IDLE = "IDLE"
    RX = "RX"  # Receiving
    TX = "TX"  # Transmitting
    ERROR = "ERROR"
    UNKNOWN = "UNKNOWN"


class NetworkStatus(str, Enum):
    """
    Network connection status for each mode.
    """

    CONNECTED = "CONNECTED"
    DISCONNECTED = "DISCONNECTED"
    CONNECTING = "CONNECTING"
    ERROR = "ERROR"
    UNKNOWN = "UNKNOWN"


class QSO(BaseModel):
    """
    Represents a single QSO (contact/transmission).

    This model captures all relevant information about a radio contact,
    including timing, participants, mode, and quality metrics.
    """

    model_config = ConfigDict(use_enum_values=True)

    # Unique identifier
    id: UUID = Field(default_factory=uuid4, description="Unique QSO identifier")

    # Timing information
    start_time: datetime = Field(
        default_factory=datetime.now, description="QSO start timestamp"
    )
    end_time: Optional[datetime] = Field(
        None, description="QSO end timestamp (None if active)"
    )
    duration_seconds: Optional[float] = Field(
        None, description="QSO duration in seconds"
    )

    # Mode and status
    mode: Mode = Field(..., description="Operating mode for this QSO")
    status: QSOStatus = Field(
        QSOStatus.STARTING, description="Current status of the QSO"
    )

    # Participants
    source_callsign: Optional[str] = Field(
        None, description="Source callsign (originating station)"
    )
    destination: Optional[str] = Field(
        None, description="Destination (callsign, talk group, reflector, etc.)"
    )

    # Mode-specific information
    slot: Optional[int] = Field(None, description="DMR slot (1 or 2)")
    talk_group: Optional[int] = Field(None, description="DMR/P25 talk group")
    source_id: Optional[int] = Field(None, description="DMR/P25 source ID")
    destination_id: Optional[int] = Field(None, description="DMR/P25 destination ID")
    reflector: Optional[str] = Field(None, description="YSF/DSTAR reflector")

    # Quality metrics
    ber: Optional[float] = Field(None, description="Bit Error Rate (percentage)")
    rssi: Optional[int] = Field(None, description="Received Signal Strength Indicator")
    loss_rate: Optional[float] = Field(None, description="Packet loss rate (percentage)")

    # Source of transmission
    rf_source: bool = Field(True, description="True if RF source, False if network")

    # Additional metadata
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional mode-specific data"
    )

    def complete(self, end_time: Optional[datetime] = None) -> None:
        """
        Mark the QSO as completed and calculate duration.

        Args:
            end_time: End time (defaults to now)
        """
        self.end_time = end_time or datetime.now()
        delta = self.end_time - self.start_time
        self.duration_seconds = delta.total_seconds()
        self.status = QSOStatus.COMPLETED

    def is_active(self) -> bool:
        """
        Check if the QSO is currently active.

        Returns:
            True if QSO is active, False otherwise
        """
        return self.status in (QSOStatus.STARTING, QSOStatus.ACTIVE)


class ModeStatus(BaseModel):
    """
    Status information for a specific mode.
    """

    model_config = ConfigDict(use_enum_values=True)

    mode: Mode
    enabled: bool = True
    network_status: NetworkStatus = NetworkStatus.UNKNOWN
    network_name: Optional[str] = None
    last_activity: Optional[datetime] = None


class SystemState(BaseModel):
    """
    Complete system state snapshot.

    This represents the entire current state of the MMDVMHost system,
    including active QSOs, mode information, and system status.
    """

    model_config = ConfigDict(use_enum_values=True)

    # Current operational state
    current_mode: Mode = Field(Mode.IDLE, description="Current active mode")
    modem_state: ModemState = Field(
        ModemState.UNKNOWN, description="Physical modem state"
    )

    # Active QSOs
    active_qsos: List[QSO] = Field(
        default_factory=list, description="Currently active QSOs"
    )

    # Mode status
    mode_status: Dict[Mode, ModeStatus] = Field(
        default_factory=dict, description="Status for each mode"
    )

    # System information
    last_update: datetime = Field(
        default_factory=datetime.now, description="Last state update timestamp"
    )
    uptime_seconds: Optional[float] = Field(
        None, description="System uptime in seconds"
    )

    # Error tracking
    error_count: int = Field(0, description="Total error count since startup")
    last_error: Optional[str] = Field(None, description="Last error message")
    last_error_time: Optional[datetime] = Field(
        None, description="Last error timestamp"
    )

    def add_active_qso(self, qso: QSO) -> None:
        """
        Add a QSO to the active list.

        Args:
            qso: QSO to add
        """
        self.active_qsos.append(qso)
        self.last_update = datetime.now()

    def remove_active_qso(self, qso_id: UUID) -> Optional[QSO]:
        """
        Remove a QSO from the active list.

        Args:
            qso_id: UUID of QSO to remove

        Returns:
            The removed QSO if found, None otherwise
        """
        for i, qso in enumerate(self.active_qsos):
            if qso.id == qso_id:
                removed = self.active_qsos.pop(i)
                self.last_update = datetime.now()
                return removed
        return None

    def get_active_qso_by_id(self, qso_id: UUID) -> Optional[QSO]:
        """
        Retrieve an active QSO by its ID.

        Args:
            qso_id: UUID of QSO to find

        Returns:
            QSO if found, None otherwise
        """
        for qso in self.active_qsos:
            if qso.id == qso_id:
                return qso
        return None

    def record_error(self, error_message: str) -> None:
        """
        Record an error in the system state.

        Args:
            error_message: Error description
        """
        self.error_count += 1
        self.last_error = error_message
        self.last_error_time = datetime.now()
        self.last_update = datetime.now()


class Event(BaseModel):
    """
    System event for WebSocket broadcasting.

    Events represent state changes that should be pushed to connected clients.
    """

    model_config = ConfigDict(use_enum_values=True)

    # Event identification
    event_id: UUID = Field(default_factory=uuid4, description="Unique event identifier")
    event_type: str = Field(..., description="Event type (qso_started, mode_changed, etc.)")
    timestamp: datetime = Field(
        default_factory=datetime.now, description="Event timestamp"
    )

    # Event data
    data: Dict[str, Any] = Field(
        default_factory=dict, description="Event-specific data"
    )

    # Severity (for filtering)
    severity: str = Field("info", description="Event severity (info, warning, error)")


class HealthStatus(BaseModel):
    """
    Application health status.

    Used for monitoring and health check endpoints.
    """

    healthy: bool = Field(..., description="Overall health status")
    version: str = Field(..., description="Application version")
    uptime_seconds: float = Field(..., description="Application uptime")

    # Component health
    log_monitor_active: bool = Field(..., description="Log monitor is running")
    state_machine_active: bool = Field(..., description="State machine is active")
    api_server_active: bool = Field(..., description="API server is running")

    # Statistics
    total_qsos_processed: int = Field(0, description="Total QSOs processed since start")
    active_websocket_connections: int = Field(
        0, description="Current WebSocket connections"
    )

    # Errors
    error_count: int = Field(0, description="Total errors since start")
    last_error: Optional[str] = Field(None, description="Most recent error")

    # Timestamps
    last_log_update: Optional[datetime] = Field(
        None, description="Last log file update processed"
    )
    current_time: datetime = Field(
        default_factory=datetime.now, description="Current server time"
    )

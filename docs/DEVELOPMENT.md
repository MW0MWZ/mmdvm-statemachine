# MMDVMHost State Machine - Development Guide

This document provides a comprehensive guide for developing and extending the MMDVMHost State Machine.

## Project Structure

```
mmdvm_state_machine/
├── README.md                   # User-facing documentation
├── DEVELOPMENT.md              # This file - developer documentation
├── requirements.txt            # Python dependencies
├── config.example.yaml         # Example configuration
├── config.yaml                 # Local configuration (gitignored)
├── setup.py                    # Package installation (TODO)
├── install.sh                  # systemd installation script (TODO)
├── mmdvm_state_machine/        # Main package
│   ├── __init__.py            # Package initialization
│   ├── __main__.py            # Application entry point
│   ├── config.py              # Configuration management
│   ├── models.py              # Data models (Pydantic)
│   ├── logging_setup.py       # Logging configuration
│   ├── state_machine.py       # State machine implementation (TODO)
│   ├── log_parser.py          # Log parsing logic (TODO)
│   ├── log_monitor.py         # inotify file monitoring (TODO)
│   ├── api_server.py          # FastAPI REST API (TODO)
│   └── websocket_manager.py   # WebSocket server (TODO)
├── tests/                      # Test suite
│   ├── __init__.py
│   ├── test_config.py
│   ├── test_models.py
│   ├── test_parser.py         # (TODO)
│   ├── test_state_machine.py  # (TODO)
│   └── fixtures/              # Test data and fixtures
│       └── sample_logs/       # Sample MMDVM log files
└── docs/                       # Additional documentation (TODO)
    ├── api.md                 # API documentation
    ├── log_formats.md         # MMDVM log format reference
    └── deployment.md          # Deployment guide
```

## Development Phases

### Phase 1: Core Infrastructure ✓ COMPLETED

**Deliverables:**
- [x] Project structure
- [x] Configuration management (YAML, Pydantic)
- [x] Data models (QSO, State, Events)
- [x] Logging setup
- [x] Main entry point skeleton

**Files Created:**
- `mmdvm_state_machine/config.py`
- `mmdvm_state_machine/models.py`
- `mmdvm_state_machine/logging_setup.py`
- `mmdvm_state_machine/__main__.py`
- `config.example.yaml`
- `requirements.txt`

### Phase 2: Log Parser (NEXT)

**Objectives:**
- Define regex patterns for each mode (DMR, D-Star, YSF, P25, NXDN, POCSAG, FM)
- Implement pattern matching and extraction
- Handle edge cases (malformed logs, unknown patterns)
- Unit tests with sample log data

**Key Components:**
1. **Pattern Definitions** (`log_parser.py`)
   - Mode-specific regex patterns
   - Common patterns (timestamps, callsigns)
   - Error patterns

2. **Parser Class** (`log_parser.py`)
   - Parse single log line
   - Extract QSO information
   - Identify state changes
   - Return structured data

3. **Tests** (`tests/test_parser.py`)
   - Test each mode's patterns
   - Edge case handling
   - Performance benchmarks

**Pattern Examples:**
```python
DMR_HEADER = re.compile(
    r"M: (\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3}) "
    r"DMR Slot (\d+), received (RF|network) voice header from "
    r"(\w+) to TG (\d+)"
)

DMR_END = re.compile(
    r"M: (\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3}) "
    r"DMR Slot (\d+), received (RF|network) end of voice transmission, "
    r"([\d.]+) seconds, BER: ([\d.]+)%"
)
```

### Phase 3: State Machine

**Objectives:**
- Thread-safe state management
- QSO lifecycle tracking
- Event generation for API/WebSocket
- Bounded QSO history (deque)

**Key Components:**
1. **StateMachine Class** (`state_machine.py`)
   - Current state (SystemState model)
   - QSO tracking (active + history)
   - Thread-safe updates (asyncio.Lock)
   - Event emission

2. **State Transitions**
   - QSO start → add to active
   - QSO end → move to history
   - Mode change → update current mode
   - Error → record in state

3. **Tests** (`tests/test_state_machine.py`)
   - Concurrent access tests
   - State transition validation
   - History size limits

### Phase 4: Log Monitor

**Objectives:**
- inotify integration for real-time monitoring
- Handle log rotation (daily files)
- Efficient file reading (only new lines)
- Reconnection/recovery logic

**Key Components:**
1. **LogMonitor Class** (`log_monitor.py`)
   - Watch directory with inotify
   - Detect new files matching pattern
   - Read new lines incrementally
   - Pass to parser → state machine

2. **File Rotation Handling**
   - Detect YYYY-MM-DD pattern changes
   - Close old file, open new file
   - Don't miss lines during transition

3. **Tests** (`tests/test_log_monitor.py`)
   - Mock file creation/writes
   - Rotation simulation
   - Error recovery

### Phase 5: REST API

**Objectives:**
- FastAPI endpoints for state queries
- Input validation (Pydantic)
- OpenAPI documentation
- Optional authentication/rate limiting

**Key Endpoints:**
- `GET /api/status` → Current SystemState
- `GET /api/qsos?limit=50&offset=0` → QSO history
- `GET /api/qsos/{id}` → Specific QSO
- `GET /api/mode` → Current mode
- `GET /api/health` → Health check

**Key Components:**
1. **APIServer Class** (`api_server.py`)
   - FastAPI app initialization
   - CORS configuration
   - Authentication middleware (if enabled)
   - Route handlers

2. **Dependency Injection**
   - Inject StateMachine instance
   - Inject Config for settings

3. **Tests** (`tests/test_api.py`)
   - Test all endpoints
   - Authentication tests
   - Error handling

### Phase 6: WebSocket Server

**Objectives:**
- WebSocket connection management
- Event broadcasting to clients
- Connection limits and timeouts
- Heartbeat/ping-pong

**Key Components:**
1. **WebSocketManager Class** (`websocket_manager.py`)
   - Track active connections
   - Broadcast events to all clients
   - Handle connect/disconnect
   - Implement ping/pong keepalive

2. **Event Types**
   - `qso_started`
   - `qso_ended`
   - `mode_changed`
   - `state_changed`
   - `error`

3. **Integration**
   - StateMachine emits events
   - WebSocketManager subscribes
   - Broadcasts to all clients

4. **Tests** (`tests/test_websocket.py`)
   - Connection tests
   - Broadcast tests
   - Max connection limit

### Phase 7: Integration & Deployment

**Objectives:**
- systemd service file
- Installation script
- Log rotation config
- Complete documentation

**Deliverables:**
1. **systemd Service** (`mmdvm-state-machine.service`)
   ```ini
   [Unit]
   Description=MMDVMHost State Machine
   After=network.target mmdvmhost.service

   [Service]
   Type=simple
   User=mmdvm
   WorkingDirectory=/opt/mmdvm-state-machine
   ExecStart=/opt/mmdvm-state-machine/venv/bin/python -m mmdvm_state_machine
   Restart=always

   [Install]
   WantedBy=multi-user.target
   ```

2. **Installation Script** (`install.sh`)
   - Create user/group
   - Set up directories
   - Install dependencies
   - Configure service
   - Set permissions

3. **Documentation**
   - API usage examples
   - WebSocket client examples
   - Troubleshooting guide

## Development Workflow

### Setting Up Development Environment

```bash
# Clone repository (or create locally)
cd /path/to/mmdvm_state_machine

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies (development mode)
pip install -r requirements.txt

# Copy example config
cp config.example.yaml config.yaml

# Edit config for development (point to test logs)
nano config.yaml
```

### Running Tests

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest --cov=mmdvm_state_machine --cov-report=html tests/

# Run specific test file
pytest tests/test_parser.py

# Run with verbose output
pytest -v tests/
```

### Code Quality

```bash
# Format code with black
black mmdvm_state_machine/

# Type checking with mypy
mypy mmdvm_state_machine/

# Lint with flake8 (optional)
flake8 mmdvm_state_machine/
```

### Running in Development

```bash
# Run with default config
python -m mmdvm_state_machine

# Run with specific config
python -m mmdvm_state_machine --config /path/to/config.yaml

# Override log level via environment
MMDVM_LOG_LEVEL=DEBUG python -m mmdvm_state_machine
```

## Testing Strategy

### Unit Tests
- Test individual components in isolation
- Mock external dependencies (files, network)
- Fast execution (< 1 second per test)

### Integration Tests
- Test component interactions
- Use test fixtures (sample log files)
- Verify end-to-end workflows

### Performance Tests
- Benchmark log parsing speed
- Test with large log files
- Verify memory usage stays bounded

### Sample Log Files

Create realistic sample logs for testing:

```bash
tests/fixtures/sample_logs/
├── MMDVM-2025-01-04.log    # DMR QSOs
├── MMDVM-2025-01-05.log    # Mixed modes
├── MMDVM-rotation.log      # Log rotation scenario
└── MMDVM-errors.log        # Error conditions
```

## Architecture Decisions

### Why inotify?
- Linux-native, kernel-level file monitoring
- Extremely efficient (no polling)
- Immediate notification of changes
- Standard on all Ubuntu Server installations

### Why FastAPI?
- Modern async framework
- Automatic OpenAPI documentation
- Built-in WebSocket support
- Excellent performance
- Type safety with Pydantic

### Why In-Memory Storage?
- No database overhead
- Fast access for API queries
- Bounded memory (configurable history size)
- Sufficient for use case (recent history only)
- Could add SQLite persistence later if needed

### Thread Safety with asyncio
- Use asyncio.Lock for state updates
- Single event loop (no thread contention)
- Immutable data structures where possible
- Copy-on-read for API responses

## Performance Targets

- **Log parsing**: < 1ms per line
- **API response**: < 10ms for status queries
- **WebSocket broadcast**: < 50ms latency
- **Memory usage**: < 100MB with 1000 QSOs in history
- **CPU usage**: < 5% on idle, < 20% during active QSO

## Security Considerations

1. **Input Validation**
   - All API inputs validated with Pydantic
   - Log lines sanitized before parsing
   - No shell execution (no shell=True)

2. **Authentication** (Optional)
   - API key authentication via headers
   - Rate limiting per client
   - CORS configuration

3. **File Permissions**
   - Read-only access to MMDVM logs
   - Write access only to own log directory
   - Run as dedicated user (not root)

4. **Network Security**
   - Bind to specific interfaces
   - Use reverse proxy (nginx) for HTTPS
   - WebSocket origin validation

## Common Development Tasks

### Adding a New Log Pattern

1. Add regex pattern to `log_parser.py`
2. Add extraction function
3. Add test case with sample log line
4. Update documentation

### Adding a New API Endpoint

1. Define response model in `models.py`
2. Add route handler in `api_server.py`
3. Add test in `tests/test_api.py`
4. Update API documentation

### Adding a New Event Type

1. Add event type to `Event` model
2. Emit from `StateMachine`
3. Handle in `WebSocketManager`
4. Document in API docs

## Troubleshooting

### Logs Not Being Parsed
- Check log file permissions
- Verify log path pattern in config
- Check inotify limits: `cat /proc/sys/fs/inotify/max_user_watches`
- Check application logs for errors

### High CPU Usage
- Profile with `py-spy`: `py-spy top -- python -m mmdvm_state_machine`
- Check regex compilation (should be compiled once)
- Verify no infinite loops in log monitoring

### Memory Growth
- Check QSO history size configuration
- Verify old QSOs are being removed from deque
- Monitor with `memory_profiler`

## Contributing

When contributing code:
1. Follow PEP 8 style guidelines
2. Add type hints to all functions
3. Write docstrings (Google style)
4. Add unit tests for new functionality
5. Update documentation

## Resources

- FastAPI: https://fastapi.tiangolo.com/
- Pydantic: https://docs.pydantic.dev/
- inotify: https://man7.org/linux/man-pages/man7/inotify.7.html
- asyncio: https://docs.python.org/3/library/asyncio.html
- MMDVMHost: https://github.com/g4klx/MMDVMHost

# Quick Start Guide

## Get Started in 5 Minutes

This guide will get you up and running with the MMDVMHost State Machine development environment.

### Prerequisites

- Python 3.8 or higher
- Ubuntu Server LTS (20.04, 22.04, or 24.04) or macOS for development
- MMDVMHost log files (or we'll create test ones)

### Step 1: Set Up Virtual Environment

```bash
cd /Users/ataylor/Library/CloudStorage/OneDrive-Personal/AI/MMDVMHost_State_Machine

# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Create Configuration

```bash
# Copy example configuration
cp config.example.yaml config.yaml

# Edit for your environment
nano config.yaml
```

**For Development/Testing**, edit these key settings:

```yaml
log_monitoring:
  log_directory: "/tmp/mmdvm-test"  # Change to a test directory
  log_path_pattern: "/tmp/mmdvm-test/MMDVM-*.log"

logging:
  level: "DEBUG"  # More verbose for development
  file: null  # Log to stdout only during development
```

### Step 3: Create Test Log Directory

```bash
# Create test directory
mkdir -p /tmp/mmdvm-test

# Create a sample log file for testing
cat > /tmp/mmdvm-test/MMDVM-2025-01-04.log << 'EOF'
M: 2025-01-04 10:00:00.000 MMDVM Host starting
M: 2025-01-04 10:00:01.000 Mode set to "IDLE"
M: 2025-01-04 10:23:45.123 DMR Slot 1, received RF voice header from G4KLX to TG 235
M: 2025-01-04 10:23:47.456 DMR Slot 1, received RF end of voice transmission, 2.3 seconds, BER: 0.5%
M: 2025-01-04 10:24:01.789 Mode set to "YSF"
EOF
```

### Step 4: Run Tests

```bash
# Run all tests
pytest tests/ -v

# Expected output: All tests pass
# ====== 35 passed in 0.53s ======
```

### Step 5: Current Status Check

```bash
# The application is ready but needs Phase 2 (Log Parser) to be functional
# Currently, the main entry point is a skeleton

# You can verify the structure:
python -m mmdvm_state_machine --help

# Expected output: Help message with version info
```

## What Works Now (Phase 1 Complete)

✅ **Configuration System**
- Load from YAML with validation
- Environment variable overrides
- Runtime validation

✅ **Data Models**
- QSO representation with all fields
- System state tracking
- Event structures for WebSocket
- Full type safety with Pydantic

✅ **Logging Infrastructure**
- Console and file logging
- Log rotation support
- Configurable levels

✅ **Test Suite**
- 35+ unit tests
- 100% coverage of Phase 1 code
- Fast execution (< 1 second)

## What's Next (Phase 2)

🚧 **Log Parser** (In Development)
- Regex patterns for each mode
- Extract QSO data from log lines
- Handle all edge cases

After parser is done, you'll be able to:
1. Monitor real MMDVM log files
2. See real-time state updates
3. Query via REST API
4. Receive WebSocket events

## Development Workflow

### Running Tests During Development

```bash
# Run tests in watch mode (requires pytest-watch)
pip install pytest-watch
ptw tests/

# Run with coverage report
pytest --cov=mmdvm_state_machine --cov-report=html tests/
# Open htmlcov/index.html in browser

# Run specific test file
pytest tests/test_models.py -v

# Run specific test
pytest tests/test_models.py::TestQSOModel::test_qso_creation_defaults -v
```

### Code Quality Checks

```bash
# Format code with black
black mmdvm_state_machine/

# Type checking
mypy mmdvm_state_machine/

# All checks before commit
black mmdvm_state_machine/ && mypy mmdvm_state_machine/ && pytest tests/
```

### Adding New Code

1. Write tests first (TDD approach)
2. Implement functionality
3. Run tests to verify
4. Format with black
5. Type check with mypy

## Project Structure Quick Reference

```
mmdvm_state_machine/
├── __init__.py           # Package exports
├── __main__.py           # Entry point (python -m mmdvm_state_machine)
├── config.py             # Configuration management
├── models.py             # Data models (QSO, State, Event, etc.)
├── logging_setup.py      # Logging configuration
│
├── log_parser.py         # TODO Phase 2
├── state_machine.py      # TODO Phase 3
├── log_monitor.py        # TODO Phase 4
├── api_server.py         # TODO Phase 5
└── websocket_manager.py  # TODO Phase 6
```

## Common Tasks

### View Available Models

```python
# In Python REPL
from mmdvm_state_machine.models import QSO, SystemState, Mode

# Create a QSO
qso = QSO(mode=Mode.DMR, source_callsign="G4KLX", talk_group=235)
print(qso.model_dump_json(indent=2))

# Create system state
state = SystemState(current_mode=Mode.DMR)
state.add_active_qso(qso)
print(f"Active QSOs: {len(state.active_qsos)}")
```

### Test Configuration Loading

```python
# In Python REPL
from mmdvm_state_machine.config import Config

# Load example config
config = Config.from_yaml("config.example.yaml")
print(f"Log directory: {config.log_monitoring.log_directory}")
print(f"API port: {config.api.port}")
print(f"QSO history size: {config.state_machine.qso_history_size}")
```

## Troubleshooting

### Import Errors

If you get `ModuleNotFoundError`:
```bash
# Make sure virtual environment is activated
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

### Test Failures

If tests fail:
```bash
# Run with verbose output to see details
pytest tests/ -vv

# Run specific failing test with print output
pytest tests/test_models.py::TestQSOModel -v -s
```

### Configuration Errors

If config validation fails:
```bash
# Check YAML syntax
python -c "import yaml; yaml.safe_load(open('config.yaml'))"

# Test config loading
python -c "from mmdvm_state_machine.config import Config; Config.from_yaml('config.yaml')"
```

## Next Steps

Ready to implement Phase 2 (Log Parser)?

See **DEVELOPMENT.md** for:
- Detailed architecture
- Phase 2 implementation plan
- Log format patterns
- Development guidelines

See **PROJECT_SUMMARY.md** for:
- Complete project overview
- All design decisions
- Performance targets
- Security model

## Getting Help

- Check **DEVELOPMENT.md** for technical details
- Review **PROJECT_SUMMARY.md** for architecture
- Look at test files for usage examples
- All functions have comprehensive docstrings

## Ready to Code!

You now have:
- ✅ Working development environment
- ✅ Configuration system
- ✅ Data models
- ✅ Test suite
- ✅ Documentation

**Next milestone**: Implement log parser (Phase 2) to start processing real MMDVM logs.

Happy coding! 73 (best regards in ham radio parlance)!

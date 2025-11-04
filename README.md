# MMDVM State Machine

A Python-based state machine and API service for MMDVMHost that monitors log files, tracks system state, and provides real-time updates via REST API and WebSocket interfaces.

## Overview

The MMDVM State Machine monitors MMDVMHost log files using inotify, maintains an in-memory database of recent QSOs (radio contacts), tracks system state, and provides both REST API and WebSocket interfaces for web applications to query current state and receive real-time updates.

### Key Features

- **Real-time Log Monitoring**: Uses inotify to efficiently monitor MMDVMHost log file changes
- **In-Memory State Database**: Maintains configurable history of recent QSOs and system events
- **REST API**: OpenAPI-compliant JSON API for querying system state, QSOs, and health status
- **WebSocket Server**: Real-time push notifications for state changes and new QSOs
- **Multi-Mode Support**: Tracks D-Star, DMR, System Fusion (YSF), P25, NXDN, POCSAG, and FM modes
- **Health Monitoring**: Built-in health checks and status reporting
- **Production Ready**: Structured logging, graceful shutdown, systemd integration

## System Requirements

- **Python**: 3.8 or higher
- **Operating System**: Linux (Debian 10+, Alpine 3.14+, Ubuntu 20.04+, or similar)
- **MMDVMHost**: Any version that produces log files
- **Memory**: Minimum 128MB RAM (configurable based on QSO history size)
- **CPU**: Any modern CPU (very low overhead)

## Installation

### Debian/Ubuntu Installation

#### 1. Install System Dependencies

```bash
# Update package index
sudo apt update

# Install Python 3.8+ and pip
sudo apt install -y python3 python3-pip python3-venv

# Install development headers (required for some Python packages)
sudo apt install -y python3-dev build-essential
```

#### 2. Create Application User (Optional but Recommended)

```bash
# Create a dedicated user for running the service
sudo useradd --system --user-group --create-home --shell /bin/bash mmdvm-api
```

#### 3. Install Application

```bash
# Clone the repository
cd /opt
sudo git clone https://github.com/MW0MWZ/mmdvm-statemachine.git
sudo chown -R mmdvm-api:mmdvm-api mmdvm-statemachine

# Switch to application user
sudo -u mmdvm-api -s

# Change to application directory
cd /opt/mmdvm-statemachine

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

#### 4. Configure the Application

```bash
# Copy example configuration
cp config.example.yaml config.yaml

# Edit configuration to match your system
nano config.yaml
```

Key settings to configure:
- `monitoring.log_file_path`: Path to MMDVMHost log file (e.g., `/var/log/mmdvm/MMDVM-2025-01-04.log`)
- `monitoring.log_directory`: Directory where MMDVMHost logs are stored
- `api.host`: API listening address (default: 127.0.0.1)
- `api.port`: API listening port (default: 8000)
- `websocket.port`: WebSocket listening port (default: 8001)

#### 5. Test the Installation

```bash
# Run the application in development mode
python -m mmdvm_statemachine --config config.yaml

# In another terminal, test the API
curl http://localhost:8000/health
curl http://localhost:8000/api/v1/state
```

#### 6. Install as systemd Service

```bash
# Exit the mmdvm-api user session
exit

# Create systemd service file
sudo nano /etc/systemd/system/mmdvm-statemachine.service
```

Add the following content:

```ini
[Unit]
Description=MMDVM State Machine API Service
After=network.target mmdvmhost.service
Wants=mmdvmhost.service

[Service]
Type=simple
User=mmdvm-api
Group=mmdvm-api
WorkingDirectory=/opt/mmdvm-statemachine
Environment="PATH=/opt/mmdvm-statemachine/venv/bin"
ExecStart=/opt/mmdvm-statemachine/venv/bin/python -m mmdvm_statemachine --config /opt/mmdvm-statemachine/config.yaml
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

Enable and start the service:

```bash
# Reload systemd configuration
sudo systemctl daemon-reload

# Enable service to start on boot
sudo systemctl enable mmdvm-statemachine

# Start the service
sudo systemctl start mmdvm-statemachine

# Check service status
sudo systemctl status mmdvm-statemachine

# View logs
sudo journalctl -u mmdvm-statemachine -f
```

### Alpine Linux Installation

#### 1. Install System Dependencies

```bash
# Update package index
sudo apk update

# Install Python 3 and pip (no build tools needed - all pure Python)
sudo apk add python3 py3-pip git
```

#### 2. Create Application User (Optional but Recommended)

```bash
# Create a dedicated user for running the service
sudo adduser -D -H -s /sbin/nologin mmdvm-api
```

#### 3. Install Application

```bash
# Clone the repository
cd /opt
sudo git clone https://github.com/MW0MWZ/mmdvm-statemachine.git
sudo chown -R mmdvm-api:mmdvm-api mmdvm-statemachine

# Change to application directory
cd /opt/mmdvm-statemachine

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

#### 4. Configure the Application

```bash
# Copy example configuration
cp config.example.yaml config.yaml

# Edit configuration to match your system
vi config.yaml
```

Configure the same settings as described in the Debian installation section.

#### 5. Test the Installation

```bash
# Run the application in development mode
python -m mmdvm_statemachine --config config.yaml

# In another terminal, test the API
wget -qO- http://localhost:8000/health
wget -qO- http://localhost:8000/api/v1/state
```

#### 6. Install as OpenRC Service

```bash
# Create OpenRC service file
sudo vi /etc/init.d/mmdvm-statemachine
```

Add the following content:

```bash
#!/sbin/openrc-run

name="MMDVM State Machine"
description="MMDVM State Machine API Service"

command="/opt/mmdvm-statemachine/venv/bin/python"
command_args="-m mmdvm_statemachine --config /opt/mmdvm-statemachine/config.yaml"
command_user="mmdvm-api:mmdvm-api"
command_background=true
pidfile="/run/${RC_SVCNAME}.pid"

directory="/opt/mmdvm-statemachine"

depend() {
    need net
    after mmdvmhost
}

start_pre() {
    checkpath --directory --owner mmdvm-api:mmdvm-api --mode 0755 /run
}
```

Make the service executable and enable it:

```bash
# Make service executable
sudo chmod +x /etc/init.d/mmdvm-statemachine

# Add service to default runlevel
sudo rc-update add mmdvm-statemachine default

# Start the service
sudo rc-service mmdvm-statemachine start

# Check service status
sudo rc-service mmdvm-statemachine status
```

## Configuration

The application uses a YAML configuration file. See `config.example.yaml` for all available options.

### Key Configuration Sections

#### Logging
```yaml
logging:
  level: INFO
  format: detailed
  file_path: /var/log/mmdvm-api/mmdvm-statemachine.log
  max_bytes: 10485760  # 10MB
  backup_count: 5
```

#### Monitoring
```yaml
monitoring:
  log_file_path: /var/log/mmdvm/MMDVM-2025-01-04.log
  log_directory: /var/log/mmdvm
  poll_interval: 1.0
  buffer_size: 8192
```

#### State Machine
```yaml
state_machine:
  max_qso_history: 1000
  qso_timeout_seconds: 300
  cleanup_interval_seconds: 60
```

#### API
```yaml
api:
  host: 127.0.0.1
  port: 8000
  cors_enabled: true
  cors_origins: ["*"]
```

#### WebSocket
```yaml
websocket:
  host: 127.0.0.1
  port: 8001
  max_connections: 100
  ping_interval: 30
```

### Environment Variable Overrides

Configuration values can be overridden using environment variables with the prefix `MMDVM_SM_`:

```bash
export MMDVM_SM_MONITORING__LOG_FILE_PATH=/custom/path/to/log
export MMDVM_SM_API__PORT=9000
export MMDVM_SM_WEBSOCKET__PORT=9001
```

## API Documentation

Once running, visit the following URLs for API documentation:

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **OpenAPI JSON**: `http://localhost:8000/openapi.json`

### Quick API Examples

```bash
# Get current system state
curl http://localhost:8000/api/v1/state

# Get recent QSOs
curl http://localhost:8000/api/v1/qsos?limit=10

# Get specific QSO by ID
curl http://localhost:8000/api/v1/qsos/{qso_id}

# Get health status
curl http://localhost:8000/health

# Get system metrics
curl http://localhost:8000/metrics
```

### WebSocket Connection

```javascript
const ws = new WebSocket('ws://localhost:8001/ws');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Event:', data.event_type, data.data);
};
```

## Development

For development setup and contribution guidelines, see:
- `docs/QUICKSTART.md` - Quick start guide
- `docs/DEVELOPMENT.md` - Development workflow and architecture
- `docs/PROJECT_SUMMARY.md` - Project architecture and design decisions

### Running Tests

```bash
# Activate virtual environment
source venv/bin/activate

# Install development dependencies
pip install pytest pytest-asyncio pytest-cov

# Run tests
pytest

# Run tests with coverage
pytest --cov=mmdvm_statemachine --cov-report=html
```

## Troubleshooting

### Service won't start

1. Check log files: `sudo journalctl -u mmdvm-statemachine -n 50` (Debian) or check `/var/log/messages` (Alpine)
2. Verify configuration file syntax: `python -m yaml config.yaml`
3. Ensure log file path exists and is readable
4. Check file permissions on the application directory

### API not responding

1. Check if service is running: `sudo systemctl status mmdvm-statemachine` (Debian) or `sudo rc-service mmdvm-statemachine status` (Alpine)
2. Verify ports are not in use: `sudo netstat -tlnp | grep -E '8000|8001'`
3. Check firewall rules if accessing remotely
4. Review API logs for errors

### High memory usage

1. Reduce `max_qso_history` in configuration
2. Decrease `cleanup_interval_seconds` for more frequent cleanup
3. Check for log parsing errors causing memory leaks

## Project Structure

```
mmdvm-statemachine/
├── src/mmdvm_statemachine/    # Source code
│   ├── __init__.py
│   ├── __main__.py             # Entry point
│   ├── models.py               # Data models
│   ├── config.py               # Configuration
│   └── logging_setup.py        # Logging configuration
├── tests/                      # Test suite
│   ├── test_models.py
│   └── test_config.py
├── docs/                       # Documentation
├── config.example.yaml         # Example configuration
├── requirements.txt            # Python dependencies
└── README.md                   # This file
```

## Contributing

Contributions are welcome! Please see the contributing guidelines in `.github/CONTRIBUTING.md` (coming soon).

## License

This project is part of the MMDVMHost ecosystem and follows the same licensing terms. See the MMDVMHost project for license details.

## Support

For issues, questions, or contributions:
- Open an issue on GitHub: https://github.com/MW0MWZ/mmdvm-statemachine/issues
- Check existing documentation in the `docs/` directory
- Review MMDVMHost documentation at https://github.com/g4klx/MMDVMHost

## Acknowledgments

- MMDVMHost project by G4KLX
- Pi-Star project for inspiration
- FastAPI and Pydantic for excellent Python frameworks

---

**Note**: This is Phase 1 of the project, implementing core infrastructure. Future phases will add log parsing, advanced state tracking, and additional features.

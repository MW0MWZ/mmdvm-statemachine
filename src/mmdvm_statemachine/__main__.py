"""
Main entry point for MMDVMHost State Machine.

This module serves as the application entry point when run as a module:
    python -m mmdvm_state_machine [--config CONFIG_PATH]

It orchestrates the startup of all components in the correct order:
1. Load configuration
2. Set up logging
3. Initialize state machine
4. Start log monitor
5. Start API server (with WebSocket support)
6. Handle graceful shutdown
"""

import argparse
import asyncio
import logging
import signal
import sys
from pathlib import Path
from typing import Optional

from mmdvm_state_machine import __version__
from mmdvm_state_machine.config import load_config, Config
from mmdvm_state_machine.logging_setup import setup_logging, get_logger

# Logger will be initialized after config is loaded
logger: Optional[logging.Logger] = None


def parse_arguments() -> argparse.Namespace:
    """
    Parse command-line arguments.

    Returns:
        Parsed arguments
    """
    parser = argparse.ArgumentParser(
        description="MMDVMHost State Machine - Real-time monitoring and API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run with default config (searches standard locations)
  python -m mmdvm_state_machine

  # Run with specific config file
  python -m mmdvm_state_machine --config /etc/mmdvm/config.yaml

  # Display version
  python -m mmdvm_state_machine --version

Environment Variables:
  MMDVM_CONFIG        Path to configuration file
  MMDVM_LOG_LEVEL     Override log level (DEBUG, INFO, WARNING, ERROR)
        """,
    )

    parser.add_argument(
        "--config",
        "-c",
        type=str,
        help="Path to configuration file (YAML)",
        default=None,
    )

    parser.add_argument(
        "--version",
        "-v",
        action="version",
        version=f"MMDVMHost State Machine v{__version__}",
    )

    return parser.parse_args()


def setup_signal_handlers(shutdown_event: asyncio.Event) -> None:
    """
    Set up signal handlers for graceful shutdown.

    Handles SIGINT (Ctrl+C) and SIGTERM (systemd stop) signals.

    Args:
        shutdown_event: Event to set on shutdown signal
    """

    def signal_handler(sig, frame):
        """Handle shutdown signal."""
        signal_name = signal.Signals(sig).name
        if logger:
            logger.info(f"Received {signal_name}, initiating graceful shutdown...")
        shutdown_event.set()

    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)


async def run_application(config: Config) -> int:
    """
    Run the main application loop.

    This is the core async function that:
    1. Initializes all components
    2. Starts all services
    3. Waits for shutdown signal
    4. Performs graceful cleanup

    Args:
        config: Application configuration

    Returns:
        Exit code (0 for success, non-zero for error)
    """
    global logger
    logger = get_logger(__name__)

    shutdown_event = asyncio.Event()
    setup_signal_handlers(shutdown_event)

    logger.info(f"Starting MMDVMHost State Machine v{__version__}")
    logger.info(f"Configuration loaded from: {config}")

    try:
        # TODO: Initialize components in Phase 2+
        # from mmdvm_state_machine.state_machine import StateMachine
        # from mmdvm_state_machine.log_monitor import LogMonitor
        # from mmdvm_state_machine.api_server import APIServer

        # state_machine = StateMachine(config.state_machine)
        # log_monitor = LogMonitor(config.log_monitoring, state_machine)
        # api_server = APIServer(config.api, config.websocket, state_machine)

        logger.info("All components initialized successfully")

        # TODO: Start services
        # await log_monitor.start()
        # await api_server.start()

        logger.info("All services started, application running")
        logger.info("Press Ctrl+C to stop")

        # Wait for shutdown signal
        await shutdown_event.wait()

        logger.info("Shutdown signal received, stopping services...")

        # TODO: Stop services gracefully
        # await api_server.stop()
        # await log_monitor.stop()

        logger.info("All services stopped gracefully")
        return 0

    except Exception as e:
        logger.error(f"Fatal error during application runtime: {e}", exc_info=True)
        return 1


def main() -> int:
    """
    Main entry point.

    Returns:
        Exit code
    """
    global logger

    try:
        # Parse arguments
        args = parse_arguments()

        # Load configuration
        try:
            config = load_config(args.config)
        except FileNotFoundError as e:
            print(f"ERROR: {e}", file=sys.stderr)
            print("\nPlease create config.yaml or specify --config", file=sys.stderr)
            print("See config.example.yaml for reference", file=sys.stderr)
            return 1
        except ValueError as e:
            print(f"ERROR: Invalid configuration: {e}", file=sys.stderr)
            return 1

        # Set up logging
        setup_logging(config.logging)
        logger = get_logger(__name__)

        # Run application
        try:
            # Use uvloop if available and enabled (Linux only)
            if config.performance.use_uvloop:
                try:
                    import uvloop
                    uvloop.install()
                    logger.info("Using uvloop for enhanced async performance")
                except ImportError:
                    logger.warning(
                        "uvloop not available, using default asyncio event loop"
                    )

            # Run the async application
            exit_code = asyncio.run(run_application(config))
            return exit_code

        except KeyboardInterrupt:
            logger.info("Interrupted by user")
            return 0

    except Exception as e:
        if logger:
            logger.critical(f"Unhandled exception: {e}", exc_info=True)
        else:
            print(f"CRITICAL: Unhandled exception: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())

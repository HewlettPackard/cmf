import logging
import os
from pathlib import Path

# Set up the root logger for cmflib
_logger = logging.getLogger("cmflib")
_logger.setLevel(logging.DEBUG)
_logger.propagate = False  # Prevent propagation to root logger to avoid duplicate messages

# Default log file location (can be overridden by environment variable)
# Following XDG Base Directory Specification for Linux/Unix systems
_default_log_dir = Path.home() / ".cache" / "cmflib"
_default_log_file = _default_log_dir / "cmflib.log"
_log_file = os.getenv("CMF_LOG_FILE", str(_default_log_file))

# Ensure log directory exists
try:
    Path(_log_file).parent.mkdir(parents=True, exist_ok=True)
except (OSError, PermissionError) as e:
    # Fallback to current working directory if we can't create the default location
    _log_file = "cmflib.log"
    _logger.warning(f"Could not create log directory, using current directory: {e}")

# File handler - captures DEBUG and above
_file_handler = logging.FileHandler(_log_file)
_file_handler.setLevel(logging.DEBUG)
_file_handler.setFormatter(logging.Formatter(
    '%(asctime)s - %(name)s - %(funcName)s - %(levelname)s - %(message)s'
))

# Console handler - captures INFO and above (skips DEBUG)
_console_handler = logging.StreamHandler()
_console_handler.setLevel(logging.INFO)
_console_handler.setFormatter(logging.Formatter(
    '%(message)s'
))

# Add handlers
_logger.addHandler(_file_handler)
_logger.addHandler(_console_handler)

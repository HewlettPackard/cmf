import logging
import os

# Set up the root logger for cmflib
_logger = logging.getLogger("cmflib")
_logger.setLevel(logging.DEBUG)
_logger.propagate = False  # Prevent propagation to root logger to avoid duplicate messages

# Default log file location (can be overridden by environment variable)
_log_file = os.getenv("CMF_LOG_FILE", "/tmp/cmflib.log")

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

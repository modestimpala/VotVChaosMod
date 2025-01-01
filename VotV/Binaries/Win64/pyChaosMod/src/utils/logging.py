import logging
from logging.handlers import RotatingFileHandler
import os
import colorama  

colorama.init()

class ColorFormatter(logging.Formatter):
    """Custom formatter with colors and styling"""

    # Color codes
    grey = "\x1b[38;21m"  # Slightly lighter grey
    white = "\x1b[37;20m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"
    dim = "\x1b[2m"  # Dimmed text
    bright = "\x1b[1m"  # Bright/bold text
    green = "\x1b[32;20m"

    # Format for different levels with smaller timestamp and better spacing
    FORMATS = {
        logging.DEBUG: (
            dim + "[%(asctime)s]" + reset + " " +
            white + "%(levelname)-8s" + reset + " " +
            dim + "%(name)s: " + reset +
            "%(message)s"
        ),
        logging.INFO: (
            dim + "[%(asctime)s]" + reset + " " +
            bright + "%(levelname)-8s" + reset + " " +
            green + "%(name)s: " + reset +
            "%(message)s"
        ),
        logging.WARNING: (
            dim + "[%(asctime)s]" + reset + " " +
            yellow + "%(levelname)-8s" + reset + " " +
            dim + "%(name)s: " + reset +
            "%(message)s"
        ),
        logging.ERROR: (
            dim + "[%(asctime)s]" + reset + " " +
            red + "%(levelname)-8s" + reset + " " +
            dim + "%(name)s: " + reset +
            "%(message)s"
        ),
        logging.CRITICAL: (
            dim + "[%(asctime)s]" + reset + " " +
            bold_red + "%(levelname)-8s" + reset + " " +
            dim + "%(name)s: " + reset +
            bright + "%(message)s" + reset
        )
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt, datefmt="%H:%M:%S")  # Shorter timestamp format
        return formatter.format(record)

def setup_logging():
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    # Set specific level for twitchio.websocket
    twitchio_logger = logging.getLogger('twitchio.websocket')
    twitchio_logger.setLevel(logging.ERROR)

    # Set specific level for websockets.server
    websocket_server_logger = logging.getLogger('websockets.server')
    websocket_server_logger.setLevel(logging.ERROR)

    # Create logs directory if it doesn't exist
    log_dir = 'logs'
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # File handler - keep original format without colors
    file_handler = RotatingFileHandler(
        filename=os.path.join(log_dir, 'chaosbot.log'),
        maxBytes=510241024,  # 5MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(
        logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    )

    # Console handler with colors
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(ColorFormatter())

    # Remove any existing handlers
    logger.handlers.clear()

    # Add the handlers to the logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger
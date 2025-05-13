import logging
import sys

RESET = "\x1b[0m"
COLORS = {
    'DEBUG': "\x1b[36m",
    'INFO': "\x1b[32m",
    'WARNING': "\x1b[33m",
    'ERROR': "\x1b[31m",
    'CRITICAL': "\x1b[41m",
}

class PrettyFormatter(logging.Formatter):
    """
    Custom formatter adding colors and a neat format.
    """
    def format(self, record):
        levelname = record.levelname
        color = COLORS.get(levelname, RESET)
        formatted = f"[{self.formatTime(record, '%Y-%m-%d %H:%M:%S')}] " \
                    f"{color}{levelname:<8}{RESET} | " \
                    f"{record.name}: {record.getMessage()}"
        if record.exc_info:
            formatted += "\n" + super().formatException(record.exc_info)
        return formatted

def get_pretty_logger(name: str, level: int = logging.DEBUG) -> logging.Logger:
    """
    Create and return a logger with colored, pretty output.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(level)
        handler.setFormatter(PrettyFormatter())
        logger.addHandler(handler)
        logger.propagate = False
    return logger

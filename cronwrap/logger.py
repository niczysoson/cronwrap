import logging
import sys
from typing import Optional

_LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
_DATE_FORMAT = "%Y-%m-%dT%H:%M:%S"


def get_logger(
    name: str,
    level: int = logging.DEBUG,
    log_file: Optional[str] = None,
) -> logging.Logger:
    """
    Return a logger configured with a stream handler and an optional file handler.

    Args:
        name: Logger name (typically the job name).
        level: Logging level.
        log_file: Optional path to a log file.

    Returns:
        Configured Logger instance.
    """
    logger = logging.getLogger(f"cronwrap.{name}")
    if logger.handlers:
        return logger

    logger.setLevel(level)
    formatter = logging.Formatter(_LOG_FORMAT, datefmt=_DATE_FORMAT)

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger

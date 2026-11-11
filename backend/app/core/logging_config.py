import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from app.core.config import BACKEND_DIR, get_settings


def configure_logging() -> logging.Logger:
    settings = get_settings()
    logs_dir = BACKEND_DIR / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)

    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    if not root_logger.handlers:
        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setFormatter(formatter)
        root_logger.addHandler(stream_handler)

        file_handler = RotatingFileHandler(
            logs_dir / "gayatri_platform.log",
            maxBytes=2_000_000,
            backupCount=3,
            encoding="utf-8",
        )
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    return logging.getLogger("gayatri_ai")

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from app_logging.filters import SensitiveURLFilter
from app_logging.formatters import build_file_formatter, build_stdout_formatter
from config.schema import LoggingConfig


def configure_logging(config: LoggingConfig) -> None:
    root = logging.getLogger()
    root.setLevel(getattr(logging, config.level.upper(), logging.INFO))
    root.handlers.clear()
    root.filters.clear()
    url_filter = SensitiveURLFilter()
    root.addFilter(url_filter)

    if config.stdout:
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(build_stdout_formatter(config.color))
        stream_handler.addFilter(url_filter)
        root.addHandler(stream_handler)

    if config.file.enabled:
        log_path = Path(config.file.path)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = RotatingFileHandler(
            log_path,
            maxBytes=config.file.rotate.max_bytes,
            backupCount=config.file.rotate.backup_count,
            encoding="utf-8",
        )
        file_handler.setFormatter(build_file_formatter())
        file_handler.addFilter(url_filter)
        root.addHandler(file_handler)

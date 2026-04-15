from __future__ import annotations

import logging
from types import ModuleType

_colorlog: ModuleType | None
try:
    import colorlog as _colorlog
except ModuleNotFoundError:  # pragma: no cover - environment dependent
    _colorlog = None

COLORLOG_MODULE: ModuleType | None = _colorlog


def build_stdout_formatter(use_color: bool) -> logging.Formatter:
    if use_color and COLORLOG_MODULE is not None:
        formatter_cls = COLORLOG_MODULE.ColoredFormatter
        return formatter_cls(
            "%(log_color)s%(asctime)s %(levelname)s %(name)s %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    return logging.Formatter(
        "%(asctime)s %(levelname)s %(name)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def build_file_formatter() -> logging.Formatter:
    return logging.Formatter(
        "%(asctime)s %(levelname)s %(name)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

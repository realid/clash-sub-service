from __future__ import annotations

import logging

try:
    from colorlog import ColoredFormatter
except ModuleNotFoundError:  # pragma: no cover - environment dependent
    ColoredFormatter = None


def build_stdout_formatter(use_color: bool) -> logging.Formatter:
    if use_color and ColoredFormatter is not None:
        return ColoredFormatter(
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

from __future__ import annotations

import argparse
import logging
from collections.abc import Sequence

from app import run_once, run_serve
from app_logging.setup import configure_logging
from config.loader import ConfigError, load_config
from exit_codes import EXIT_CONFIG_ERROR, EXIT_OK, EXIT_RUNTIME_ERROR


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="clash-sub-service")
    subparsers = parser.add_subparsers(dest="command", required=True)

    for command in ("serve", "once", "validate-config"):
        sub = subparsers.add_parser(command)
        sub.add_argument("-c", "--config", required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    try:
        config = load_config(args.config)
    except ConfigError:
        return EXIT_CONFIG_ERROR

    configure_logging(config.logging)
    logger = logging.getLogger(__name__)

    if args.command == "validate-config":
        logger.info("配置校验成功")
        return EXIT_OK

    try:
        if args.command == "once":
            run_once(config)
            return EXIT_OK
        if args.command == "serve":
            return run_serve(args.config, config)
    except Exception as exc:  # pragma: no cover - covered by CLI tests
        logger.error("运行失败 error=%s", exc)
        return EXIT_RUNTIME_ERROR
    return EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

import logging
import os
import threading
from pathlib import Path

from app_logging.setup import configure_logging
from config.schema import AppConfig
from core.fetcher import fetch_subscription_text
from core.generator import generate_from_subscription_body
from local_http.server import LocalHTTPServer
from service.config_watcher import ConfigWatcher
from service.runner import ServiceRunner
from service.state import ServiceState


class RuntimeConfigManager:
    def __init__(self, config_path: str, config: AppConfig) -> None:
        self.config_path = config_path
        self._config = config
        self._lock = threading.Lock()
        self._fingerprint = self.read_fingerprint()

    def current(self) -> AppConfig:
        with self._lock:
            return self._config

    def update(self, config: AppConfig) -> None:
        with self._lock:
            self._config = config
            self._fingerprint = self.read_fingerprint()

    def current_interval(self) -> int:
        return self.current().server.refresh_interval

    def current_fingerprint(self) -> tuple[int, int] | None:
        with self._lock:
            return self._fingerprint

    def read_fingerprint(self) -> tuple[int, int] | None:
        try:
            stat_result = os.stat(self.config_path)
        except OSError:
            return None
        return (stat_result.st_mtime_ns, stat_result.st_size)


def build_refresh_callable(manager: RuntimeConfigManager):
    def refresh() -> tuple[int, str]:
        config = manager.current()
        body = fetch_subscription_text(
            config.subscription.url,
            timeout=config.subscription.timeout,
        )
        result = generate_from_subscription_body(
            body,
            port=config.clash.port,
            allow_lan=config.clash.allow_lan,
        )
        output_path = Path(config.output.path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(result.yaml_text, encoding="utf-8")
        return result.node_count, result.yaml_text

    return refresh


def run_once(config: AppConfig) -> str:
    body = fetch_subscription_text(
        config.subscription.url,
        timeout=config.subscription.timeout,
    )
    result = generate_from_subscription_body(
        body,
        port=config.clash.port,
        allow_lan=config.clash.allow_lan,
    )
    output_path = Path(config.output.path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(result.yaml_text, encoding="utf-8")
    return result.yaml_text


def run_serve(config_path: str, config: AppConfig) -> int:
    configure_logging(config.logging)
    logger = logging.getLogger(__name__)
    logger.info("服务入口 mode=serve")

    state = ServiceState()
    manager = RuntimeConfigManager(config_path, config)
    refresh_callable = build_refresh_callable(manager)

    def refresh_on_config_reload() -> None:
        try:
            node_count, yaml_text = refresh_callable()
            state.update_success(yaml_text, node_count)
            logger.info("配置变更后立即刷新成功 nodes=%s", node_count)
        except Exception as exc:
            state.update_error(str(exc))
            logger.error("配置变更后立即刷新失败 error=%s", exc)

    watcher = ConfigWatcher(manager, on_reload=refresh_on_config_reload)
    runner = ServiceRunner(
        state,
        refresh_callable,
        interval_getter=manager.current_interval,
    )
    server = LocalHTTPServer(
        state,
        listen=config.server.listen,
        port=config.server.port,
        access_log=config.logging.access_log,
    )

    watcher.start()
    runner.start()
    try:
        server.start()
    except KeyboardInterrupt:
        logger.info("收到停止信号")
    finally:
        server.stop()
        runner.stop()
        watcher.stop()
    return 0

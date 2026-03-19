from __future__ import annotations

import logging
import threading
from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING

from config.loader import ConfigError, load_config

try:
    from watchdog.events import FileSystemEventHandler
    from watchdog.observers import Observer
except ModuleNotFoundError:  # pragma: no cover - environment dependent
    FileSystemEventHandler = object
    Observer = None

if TYPE_CHECKING:
    from app import RuntimeConfigManager
    from config.schema import AppConfig


class ConfigWatcher:
    def __init__(
        self,
        manager: "RuntimeConfigManager",
        *,
        poll_interval: float = 1.0,
        debounce_interval: float = 0.5,
        loader: Callable[[str], "AppConfig"] = load_config,
        on_reload: Callable[[], None] | None = None,
    ) -> None:
        self._manager = manager
        self._poll_interval = max(0.1, float(poll_interval))
        self._debounce_interval = max(0.0, float(debounce_interval))
        self._loader = loader
        self._on_reload = on_reload
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._observer = None
        self._debounce_timer: threading.Timer | None = None
        self._debounce_lock = threading.Lock()
        self._logger = logging.getLogger(__name__)
        self._config_path = Path(manager.config_path).resolve()

    def start(self) -> None:
        if self._observer is not None or (self._thread and self._thread.is_alive()):
            return
        self._stop_event.clear()
        if Observer is not None:
            self._start_watchdog()
            self._logger.info("配置文件监控已启动 path=%s backend=watchdog", self._manager.config_path)
            return
        self._thread = threading.Thread(target=self._run_polling, name="config-watcher", daemon=True)
        self._thread.start()
        self._logger.info("配置文件监控已启动 path=%s backend=polling", self._manager.config_path)

    def stop(self) -> None:
        self._stop_event.set()
        with self._debounce_lock:
            if self._debounce_timer is not None:
                self._debounce_timer.cancel()
                self._debounce_timer = None
        if self._observer is not None:
            self._observer.stop()
            self._observer.join(timeout=5)
            self._observer = None
        if self._thread:
            self._thread.join(timeout=5)
            self._thread = None
        self._logger.info("配置文件监控已停止")

    def _start_watchdog(self) -> None:
        assert Observer is not None
        observer = Observer()
        observer.schedule(_ConfigFileEventHandler(self), str(self._config_path.parent), recursive=False)
        observer.start()
        self._observer = observer

    def _run_polling(self) -> None:
        while not self._stop_event.wait(self._poll_interval):
            self._check_once()

    def _check_once(self) -> None:
        current = self._manager.current_fingerprint()
        latest = self._manager.read_fingerprint()
        if latest == current:
            return
        self._logger.info("检测到配置文件变更 path=%s", self._manager.config_path)
        try:
            config = self._loader(self._manager.config_path)
        except ConfigError as exc:
            self._logger.warning("配置重载失败，继续使用旧配置 error=%s", exc)
            return
        self._manager.update(config)
        self._logger.info(
            "配置文件重读成功 subscription_url=%s refresh_interval=%s clash_port=%s",
            config.subscription.url,
            config.server.refresh_interval,
            config.clash.port,
        )
        if self._on_reload is not None:
            self._on_reload()

    def _handle_watchdog_event(self, src_path: str) -> None:
        event_path = Path(src_path).resolve()
        if event_path != self._config_path:
            return
        with self._debounce_lock:
            if self._debounce_timer is not None:
                self._debounce_timer.cancel()
            self._debounce_timer = threading.Timer(self._debounce_interval, self._run_debounced_check)
            self._debounce_timer.daemon = True
            self._debounce_timer.start()

    def _run_debounced_check(self) -> None:
        with self._debounce_lock:
            self._debounce_timer = None
        if not self._stop_event.is_set():
            self._check_once()


class _ConfigFileEventHandler(FileSystemEventHandler):
    def __init__(self, watcher: ConfigWatcher) -> None:
        super().__init__()
        self._watcher = watcher

    def on_modified(self, event) -> None:  # type: ignore[override]
        if getattr(event, "is_directory", False):
            return
        self._watcher._handle_watchdog_event(event.src_path)

    def on_created(self, event) -> None:  # type: ignore[override]
        if getattr(event, "is_directory", False):
            return
        self._watcher._handle_watchdog_event(event.src_path)

    def on_moved(self, event) -> None:  # type: ignore[override]
        if getattr(event, "is_directory", False):
            return
        self._watcher._handle_watchdog_event(event.dest_path)

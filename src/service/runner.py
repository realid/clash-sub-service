from __future__ import annotations

import logging
import threading
from collections.abc import Callable

from service.state import ServiceState


class ServiceRunner:
    def __init__(
        self,
        state: ServiceState,
        refresh_callable: Callable[[], tuple[int, str]],
        *,
        interval: int = 300,
        interval_getter: Callable[[], int] | None = None,
    ) -> None:
        self._state = state
        self._refresh_callable = refresh_callable
        self._interval = interval
        self._interval_getter = interval_getter
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._logger = logging.getLogger(__name__)

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, name="refresh-runner", daemon=True)
        self._thread.start()
        self._logger.info("后台刷新服务已启动")

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=5)
        self._logger.info("后台刷新服务已停止")

    def _run(self) -> None:
        while not self._stop_event.is_set():
            try:
                node_count, yaml_text = self._refresh_callable()
                self._state.update_success(yaml_text, node_count)
                self._logger.info("订阅刷新成功 nodes=%s", node_count)
            except Exception as exc:  # pragma: no cover - guarded by tests
                self._state.update_error(str(exc))
                self._logger.error("订阅刷新失败 error=%s", exc)
            interval = self._current_interval()
            if self._stop_event.wait(interval):
                break

    def _current_interval(self) -> int:
        if self._interval_getter is not None:
            return max(1, int(self._interval_getter()))
        return max(1, int(self._interval))

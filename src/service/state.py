from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from threading import Lock


@dataclass(slots=True)
class StateSnapshot:
    ready: bool
    yaml_text: str
    node_count: int
    error: str
    updated_at: datetime | None
    refresh_count: int


class ServiceState:
    def __init__(self) -> None:
        self._lock = Lock()
        self._yaml_text = ""
        self._node_count = 0
        self._error = ""
        self._ready = False
        self._updated_at: datetime | None = None
        self._refresh_count = 0

    def update_success(self, yaml_text: str, node_count: int) -> None:
        with self._lock:
            self._yaml_text = yaml_text
            self._node_count = node_count
            self._error = ""
            self._ready = True
            self._updated_at = datetime.now(timezone.utc)
            self._refresh_count += 1

    def update_error(self, error: str) -> None:
        with self._lock:
            self._error = error
            self._ready = False
            self._updated_at = datetime.now(timezone.utc)
            self._refresh_count += 1

    def snapshot(self) -> StateSnapshot:
        with self._lock:
            return StateSnapshot(
                ready=self._ready,
                yaml_text=self._yaml_text,
                node_count=self._node_count,
                error=self._error,
                updated_at=self._updated_at,
                refresh_count=self._refresh_count,
            )

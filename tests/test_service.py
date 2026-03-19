from __future__ import annotations

import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from app import RuntimeConfigManager
from config.loader import ConfigError
from config.schema import AppConfig
from service.config_watcher import ConfigWatcher
from service.runner import ServiceRunner
from service.state import ServiceState


def _build_config(
    *,
    subscription_url: str,
    refresh_interval: int,
    clash_port: int,
) -> AppConfig:
    return AppConfig.from_dict(
        {
            "subscription": {
                "url": subscription_url,
                "timeout": 15,
            },
            "output": {
                "path": "/tmp/clash.yaml",
            },
            "server": {
                "listen": "127.0.0.1",
                "port": 9095,
                "refresh_interval": refresh_interval,
            },
            "clash": {
                "port": clash_port,
                "allow_lan": True,
            },
            "logging": {
                "level": "INFO",
                "format": "text",
                "stdout": False,
                "color": False,
                "access_log": True,
                "file": {
                    "enabled": False,
                    "path": "/tmp/app.log",
                    "rotate": {
                        "type": "size",
                        "max_bytes": 1024,
                        "backup_count": 1,
                    },
                },
            },
        }
    )


class ServiceStateTestCase(unittest.TestCase):
    def test_snapshot_ready_after_success(self) -> None:
        state = ServiceState()

        state.update_success("port: 1082\n", 2)
        snapshot = state.snapshot()

        self.assertTrue(snapshot.ready)
        self.assertEqual(snapshot.node_count, 2)
        self.assertEqual(snapshot.error, "")
        self.assertEqual(snapshot.refresh_count, 1)

    def test_snapshot_preserves_last_yaml_on_error(self) -> None:
        state = ServiceState()

        state.update_success("port: 1082\n", 1)
        state.update_error("network down")
        snapshot = state.snapshot()

        self.assertEqual(snapshot.yaml_text, "port: 1082\n")
        self.assertEqual(snapshot.error, "network down")
        self.assertFalse(snapshot.ready)
        self.assertEqual(snapshot.refresh_count, 2)


class ServiceRunnerTestCase(unittest.TestCase):
    def test_runner_refreshes_immediately_and_periodically(self) -> None:
        state = ServiceState()
        calls = []
        event = threading.Event()

        def refresh_callable() -> tuple[int, str]:
            calls.append(time.time())
            event.set()
            return 1, "port: 1082\n"

        runner = ServiceRunner(state, refresh_callable, interval=1)
        runner.start()
        try:
            self.assertTrue(event.wait(1.0))
            time.sleep(1.2)
            snapshot = state.snapshot()
            self.assertGreaterEqual(len(calls), 2)
            self.assertTrue(snapshot.ready)
            self.assertEqual(snapshot.node_count, 1)
        finally:
            runner.stop()

    def test_runner_records_refresh_error(self) -> None:
        state = ServiceState()
        event = threading.Event()

        def refresh_callable() -> tuple[int, str]:
            event.set()
            raise RuntimeError("refresh failed")

        runner = ServiceRunner(state, refresh_callable, interval=1)
        runner.start()
        try:
            self.assertTrue(event.wait(1.0))
            time.sleep(0.1)
            snapshot = state.snapshot()
            self.assertEqual(snapshot.error, "refresh failed")
            self.assertEqual(snapshot.refresh_count, 1)
        finally:
            runner.stop()

    def test_runner_uses_dynamic_interval_getter(self) -> None:
        state = ServiceState()
        calls = []
        intervals = {"value": 2}
        first_call = threading.Event()

        def refresh_callable() -> tuple[int, str]:
            calls.append(time.time())
            if len(calls) == 1:
                intervals["value"] = 1
                first_call.set()
            return 1, "port: 1082\n"

        runner = ServiceRunner(
            state,
            refresh_callable,
            interval_getter=lambda: intervals["value"],
        )
        runner.start()
        try:
            self.assertTrue(first_call.wait(1.0))
            time.sleep(1.3)
            self.assertGreaterEqual(len(calls), 2)
        finally:
            runner.stop()


class ConfigWatcherTestCase(unittest.TestCase):
    @patch("service.config_watcher.Observer", None)
    def test_watcher_reloads_config_after_file_change(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.yaml"
            config_path.write_text("version: 1\n", encoding="utf-8")
            initial_config = _build_config(
                subscription_url="https://old.example/subscription",
                refresh_interval=300,
                clash_port=1082,
            )
            updated_config = _build_config(
                subscription_url="https://new.example/subscription",
                refresh_interval=120,
                clash_port=7890,
            )
            manager = RuntimeConfigManager(str(config_path), initial_config)
            event = threading.Event()

            def loader(_: str) -> AppConfig:
                event.set()
                return updated_config

            on_reload_mock = []

            watcher = ConfigWatcher(
                manager,
                poll_interval=0.1,
                loader=loader,
                on_reload=lambda: on_reload_mock.append("called"),
            )
            watcher.start()
            try:
                time.sleep(0.15)
                config_path.write_text("version: 2\n", encoding="utf-8")
                self.assertTrue(event.wait(1.0))
                time.sleep(0.1)
            finally:
                watcher.stop()

            self.assertEqual(manager.current().subscription.url, "https://new.example/subscription")
            self.assertEqual(manager.current_interval(), 120)
            self.assertEqual(on_reload_mock, ["called"])

    @patch("service.config_watcher.Observer", None)
    def test_watcher_keeps_previous_config_when_reload_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.yaml"
            config_path.write_text("version: 1\n", encoding="utf-8")
            initial_config = _build_config(
                subscription_url="https://old.example/subscription",
                refresh_interval=300,
                clash_port=1082,
            )
            manager = RuntimeConfigManager(str(config_path), initial_config)
            event = threading.Event()

            def loader(_: str) -> AppConfig:
                event.set()
                raise ConfigError("bad config")

            watcher = ConfigWatcher(manager, poll_interval=0.1, loader=loader)
            watcher.start()
            try:
                time.sleep(0.15)
                config_path.write_text("version: 2\n", encoding="utf-8")
                self.assertTrue(event.wait(1.0))
                time.sleep(0.1)
            finally:
                watcher.stop()

            self.assertEqual(manager.current().subscription.url, "https://old.example/subscription")
            self.assertEqual(manager.current_interval(), 300)

    @patch("service.config_watcher.Observer", None)
    def test_watcher_stops_cleanly(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.yaml"
            config_path.write_text("version: 1\n", encoding="utf-8")
            manager = RuntimeConfigManager(
                str(config_path),
                _build_config(
                    subscription_url="https://old.example/subscription",
                    refresh_interval=300,
                    clash_port=1082,
                ),
            )
            watcher = ConfigWatcher(manager, poll_interval=0.1)
            watcher.start()
            watcher.stop()

            self.assertIsNone(watcher._thread)

    def test_watcher_prefers_watchdog_backend_when_available(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.yaml"
            config_path.write_text("version: 1\n", encoding="utf-8")
            manager = RuntimeConfigManager(
                str(config_path),
                _build_config(
                    subscription_url="https://old.example/subscription",
                    refresh_interval=300,
                    clash_port=1082,
                ),
            )

            class FakeObserver:
                def __init__(self) -> None:
                    self.scheduled = None
                    self.started = False
                    self.stopped = False
                    self.joined = False

                def schedule(self, handler, path: str, recursive: bool) -> None:
                    self.scheduled = (handler, path, recursive)

                def start(self) -> None:
                    self.started = True

                def stop(self) -> None:
                    self.stopped = True

                def join(self, timeout: float | None = None) -> None:
                    self.joined = True

            fake_observer = FakeObserver()

            with patch("service.config_watcher.Observer", return_value=fake_observer):
                watcher = ConfigWatcher(manager, poll_interval=0.1)
                watcher.start()
                watcher.stop()

            self.assertTrue(fake_observer.started)
            self.assertTrue(fake_observer.stopped)
            self.assertTrue(fake_observer.joined)
            self.assertEqual(fake_observer.scheduled[1], str(config_path.parent.resolve()))
            self.assertFalse(fake_observer.scheduled[2])
            self.assertIsNone(watcher._thread)

    def test_watchdog_handler_ignores_other_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.yaml"
            config_path.write_text("version: 1\n", encoding="utf-8")
            manager = RuntimeConfigManager(
                str(config_path),
                _build_config(
                    subscription_url="https://old.example/subscription",
                    refresh_interval=300,
                    clash_port=1082,
                ),
            )
            watcher = ConfigWatcher(manager, poll_interval=0.1)

            class FakeTimer:
                created = []

                def __init__(self, interval: float, fn) -> None:
                    self.interval = interval
                    self.fn = fn
                    self.daemon = False
                    self.cancelled = False
                    FakeTimer.created.append(self)

                def cancel(self) -> None:
                    self.cancelled = True

                def start(self) -> None:
                    return

            with patch("service.config_watcher.threading.Timer", FakeTimer):
                with patch.object(watcher, "_check_once") as check_once_mock:
                    watcher._handle_watchdog_event(str(config_path.parent / "other.yaml"))
                    watcher._handle_watchdog_event(str(config_path))
                    FakeTimer.created[-1].fn()

                check_once_mock.assert_called_once()

    def test_watchdog_events_are_debounced(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.yaml"
            config_path.write_text("version: 1\n", encoding="utf-8")
            manager = RuntimeConfigManager(
                str(config_path),
                _build_config(
                    subscription_url="https://old.example/subscription",
                    refresh_interval=300,
                    clash_port=1082,
                ),
            )
            watcher = ConfigWatcher(manager, debounce_interval=1.0)

            class FakeTimer:
                created = []

                def __init__(self, interval: float, fn) -> None:
                    self.interval = interval
                    self.fn = fn
                    self.daemon = False
                    self.cancelled = False
                    FakeTimer.created.append(self)

                def cancel(self) -> None:
                    self.cancelled = True

                def start(self) -> None:
                    return

            with patch("service.config_watcher.threading.Timer", FakeTimer):
                watcher._handle_watchdog_event(str(config_path))
                watcher._handle_watchdog_event(str(config_path))

            self.assertEqual(len(FakeTimer.created), 2)
            self.assertTrue(FakeTimer.created[0].cancelled)
            self.assertFalse(FakeTimer.created[1].cancelled)


if __name__ == "__main__":
    unittest.main()

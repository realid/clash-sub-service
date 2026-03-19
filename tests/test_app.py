from __future__ import annotations

import unittest
from unittest.mock import patch

from app import RuntimeConfigManager, build_refresh_callable
from config.schema import AppConfig


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


class RuntimeConfigManagerTestCase(unittest.TestCase):
    def test_refresh_uses_current_subscription_config(self) -> None:
        config = _build_config(
            subscription_url="https://old.example/subscription",
            refresh_interval=300,
            clash_port=1082,
        )
        manager = RuntimeConfigManager("/tmp/config.yaml", config)

        with patch(
            "app.fetch_subscription_text",
            return_value="c3M6Ly9ZV1Z6TFRJMU5pMW5ZMjA2Y0dGemMwQmxlR0Z0Y0d4bExtTnZiVG8wTkRNPQ==",
        ) as fetch_mock:
            refresh = build_refresh_callable(manager)
            node_count, yaml_text = refresh()

        self.assertEqual(fetch_mock.call_args.args[0], "https://old.example/subscription")
        self.assertEqual(node_count, 1)
        self.assertIn("port: 1082", yaml_text)

    def test_refresh_uses_updated_runtime_config(self) -> None:
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
        manager = RuntimeConfigManager("/tmp/config.yaml", initial_config)
        manager.update(updated_config)

        with patch(
            "app.fetch_subscription_text",
            return_value="c3M6Ly9ZV1Z6TFRJMU5pMW5ZMjA2Y0dGemMwQmxlR0Z0Y0d4bExtTnZiVG8wTkRNPQ==",
        ) as fetch_mock:
            refresh = build_refresh_callable(manager)
            node_count, yaml_text = refresh()

        self.assertEqual(fetch_mock.call_args.args[0], "https://new.example/subscription")
        self.assertEqual(node_count, 1)
        self.assertEqual(manager.current_interval(), 120)
        self.assertIn("port: 7890", yaml_text)

    def test_manager_tracks_fingerprint_after_update(self) -> None:
        config = _build_config(
            subscription_url="https://old.example/subscription",
            refresh_interval=300,
            clash_port=1082,
        )
        manager = RuntimeConfigManager("/tmp/config.yaml", config)

        with patch("app.os.stat") as stat_mock:
            stat_mock.return_value.st_mtime_ns = 20
            stat_mock.return_value.st_size = 100
            manager.update(config)

        self.assertEqual(manager.current_fingerprint(), (20, 100))

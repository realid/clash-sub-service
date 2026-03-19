from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from cli import main
from exit_codes import EXIT_OK, EXIT_RUNTIME_ERROR


def _write_config(path: Path, output_path: Path) -> None:
    path.write_text(
        "\n".join(
            [
                "subscription:",
                '  url: "https://example.invalid/subscription"',
                "  timeout: 15",
                "output:",
                f'  path: "{output_path}"',
                "server:",
                '  listen: "127.0.0.1"',
                "  port: 9095",
                "  refresh_interval: 300",
                "clash:",
                "  port: 1082",
                "  allow_lan: true",
                "logging:",
                '  level: "INFO"',
                '  format: "text"',
                "  stdout: false",
                "  color: false",
                "  access_log: true",
                "  file:",
                "    enabled: false",
                '    path: "./logs/test.log"',
                "    rotate:",
                '      type: "size"',
                "      max_bytes: 1024",
                "      backup_count: 1",
            ]
        ),
        encoding="utf-8",
    )


class CLITestCase(unittest.TestCase):
    def test_once_writes_yaml_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.yaml"
            output_path = Path(tmpdir) / "out.yaml"
            _write_config(config_path, output_path)

            with patch(
                "app.fetch_subscription_text",
                return_value="c3M6Ly9ZV1Z6TFRJMU5pMW5ZMjA2Y0dGemMwQmxlR0Z0Y0d4bExtTnZiVG8wTkRNPQ==",
            ):
                exit_code = main(["once", "-c", str(config_path)])

            self.assertEqual(exit_code, EXIT_OK)
            self.assertTrue(output_path.exists())
            self.assertIn("proxies:", output_path.read_text(encoding="utf-8"))

    def test_serve_invokes_runtime(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.yaml"
            output_path = Path(tmpdir) / "out.yaml"
            _write_config(config_path, output_path)

            with patch("cli.run_serve", return_value=0) as run_serve_mock:
                exit_code = main(["serve", "-c", str(config_path)])

            self.assertEqual(exit_code, EXIT_OK)
            run_serve_mock.assert_called_once()

    def test_once_returns_runtime_error_when_generation_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.yaml"
            output_path = Path(tmpdir) / "out.yaml"
            _write_config(config_path, output_path)

            with patch(
                "app.fetch_subscription_text",
                return_value="bm90LWEtbm9kZQ==",
            ):
                exit_code = main(["once", "-c", str(config_path)])

            self.assertEqual(exit_code, EXIT_RUNTIME_ERROR)


if __name__ == "__main__":
    unittest.main()

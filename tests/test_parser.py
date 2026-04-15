from __future__ import annotations

import base64
import json
import unittest

from core.parser import (
    b64decode_any,
    parse_node,
    parse_ss,
    parse_vmess,
    split_subscription_lines,
)


class ParserTestCase(unittest.TestCase):
    def test_b64decode_any_supports_missing_padding(self) -> None:
        encoded = base64.b64encode(b"hello").decode("utf-8").rstrip("=")
        decoded = b64decode_any(encoded)
        self.assertEqual(decoded, b"hello")

    def test_split_subscription_lines_filters_invalid_lines(self) -> None:
        body = "\n".join(
            [
                "ss://YWVzLTI1Ni1nY206cGFzc0BleGFtcGxlLmNvbTo0NDM=#demo",
                "not-a-node",
                "",
                "vmess://eyJhZGQiOiJ2bWVzcy5leGFtcGxlLmNvbSIsInBvcnQiOiI0NDMiLCJpZCI6InV1aWQtMTIzIiwiYWlkIjoiMCIsIm5ldCI6InRjcCIsInBzIjoidm1lc3MtZGVtbyJ9",
            ]
        )
        encoded = base64.b64encode(body.encode("utf-8")).decode("utf-8")

        lines = split_subscription_lines(encoded)

        self.assertEqual(len(lines), 2)
        self.assertTrue(lines[0].startswith("ss://"))
        self.assertTrue(lines[1].startswith("vmess://"))

    def test_parse_ss_supports_tag_and_base64_payload(self) -> None:
        node = parse_ss("ss://YWVzLTI1Ni1nY206cGFzc0BleGFtcGxlLmNvbTo0NDM=#demo")

        self.assertIsNotNone(node)
        self.assertEqual(node.name, "demo")
        self.assertEqual(node.data["type"], "ss")
        self.assertEqual(node.data["server"], "example.com")
        self.assertEqual(node.data["port"], 443)

    def test_parse_vmess_supports_ws_and_tls(self) -> None:
        payload = {
            "v": "2",
            "ps": "vmess-demo",
            "add": "vmess.example.com",
            "port": "443",
            "id": "uuid-123",
            "aid": "0",
            "net": "ws",
            "tls": "tls",
            "path": "/ws",
            "host": "cdn.example.com",
        }
        encoded = base64.b64encode(json.dumps(payload).encode("utf-8")).decode("utf-8")

        node = parse_vmess(f"vmess://{encoded}")

        self.assertIsNotNone(node)
        self.assertEqual(node.name, "vmess-demo")
        self.assertEqual(node.data["type"], "vmess")
        self.assertEqual(node.data["network"], "ws")
        self.assertTrue(node.data["tls"])
        self.assertEqual(node.data["ws-opts"]["path"], "/ws")
        self.assertEqual(node.data["ws-opts"]["headers"]["Host"], "cdn.example.com")

    def test_parse_node_returns_none_for_unsupported_protocol(self) -> None:
        self.assertIsNone(parse_node("trojan://example"))


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import base64
import unittest

from core.clash_builder import build_clash_config, dump_clash_yaml
from core.generator import GenerationError, generate_from_subscription_body
from models.node import Node


class ClashBuilderTestCase(unittest.TestCase):
    def test_build_clash_config_with_allow_lan(self) -> None:
        nodes = [
            Node(
                name="demo-ss",
                data={
                    "name": "demo-ss",
                    "type": "ss",
                    "server": "example.com",
                    "port": 443,
                    "cipher": "aes-256-gcm",
                    "password": "pass",
                    "udp": True,
                },
            )
        ]

        config = build_clash_config(nodes, port=1082, allow_lan=True)

        self.assertEqual(config["port"], 1082)
        self.assertEqual(config["socks-port"], 1083)
        self.assertTrue(config["allow-lan"])
        self.assertEqual(config["bind-address"], "*")
        self.assertEqual(config["proxy-groups"][0]["proxies"], ["demo-ss"])

    def test_dump_clash_yaml_preserves_expected_keys(self) -> None:
        config = {
            "port": 1082,
            "socks-port": 1083,
            "allow-lan": True,
            "proxies": [{"name": "demo-ss", "type": "ss"}],
        }

        yaml_text = dump_clash_yaml(config)

        self.assertIn("port: 1082", yaml_text)
        self.assertIn("socks-port: 1083", yaml_text)
        self.assertIn("allow-lan: true", yaml_text)

    def test_generate_from_subscription_body_builds_yaml(self) -> None:
        body = "ss://YWVzLTI1Ni1nY206cGFzc0BleGFtcGxlLmNvbTo0NDM=#demo"
        encoded = base64.b64encode(body.encode("utf-8")).decode("utf-8")

        result = generate_from_subscription_body(encoded, port=7890, allow_lan=False)

        self.assertEqual(result.node_count, 1)
        self.assertEqual(result.config["port"], 7890)
        self.assertFalse(result.config["allow-lan"])
        self.assertNotIn("bind-address", result.config)
        self.assertIn("demo", result.yaml_text)

    def test_generate_from_subscription_body_rejects_empty_result(self) -> None:
        encoded = base64.b64encode(b"not-a-node").decode("utf-8")

        with self.assertRaises(GenerationError) as ctx:
            generate_from_subscription_body(encoded)

        self.assertIn("解析结果为空", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import yaml

from models.node import Node


def build_clash_config(
    nodes: list[Node],
    *,
    port: int = 1082,
    allow_lan: bool = True,
) -> dict[str, object]:
    proxy_names = [node.name for node in nodes]
    config: dict[str, object] = {
        "port": port,
        "socks-port": port + 1,
        "allow-lan": allow_lan,
        "mode": "rule",
        "log-level": "warning",
        "external-controller": "127.0.0.1:9090",
        "proxies": [node.data for node in nodes],
        "proxy-groups": [
            {
                "name": "MANUAL",
                "type": "select",
                "proxies": proxy_names,
            }
        ],
        "rules": [
            "GEOIP,LAN,DIRECT,no-resolve",
            "GEOIP,CN,DIRECT",
            "MATCH,MANUAL",
        ],
    }
    if allow_lan:
        config["bind-address"] = "*"
    return config


def dump_clash_yaml(config: dict[str, object]) -> str:
    return yaml.safe_dump(
        config,
        allow_unicode=True,
        sort_keys=False,
        default_flow_style=False,
    )

from __future__ import annotations

import base64
import json
from urllib.parse import unquote

from models.node import Node


def b64decode_any(value: str) -> bytes:
    text = value.strip()
    padding = (-len(text)) % 4
    if padding:
        text += "=" * padding
    return base64.b64decode(text)


def split_subscription_lines(body: str) -> list[str]:
    decoded = b64decode_any(body).decode("utf-8", errors="ignore")
    normalized = decoded.replace("\r\n", "\n").replace("\r", "\n")
    result: list[str] = []
    for line in normalized.splitlines():
        candidate = line.strip()
        if candidate.startswith(("ss://", "vmess://")):
            result.append(candidate)
    return result


def parse_ss(line: str) -> Node | None:
    payload = line[5:]
    if "#" in payload:
        payload, tag = payload.split("#", 1)
        name = unquote(tag) or ""
    else:
        name = ""
    try:
        decoded = b64decode_any(payload).decode("utf-8")
        method_password, server_port = decoded.rsplit("@", 1)
        cipher, password = method_password.split(":", 1)
        server, port_text = server_port.rsplit(":", 1)
        port = int(port_text)
    except (ValueError, UnicodeDecodeError):
        return None
    node_name = name or f"ss@{server}:{port}"
    return Node(
        name=node_name,
        data={
            "name": node_name,
            "type": "ss",
            "server": server,
            "port": port,
            "cipher": cipher,
            "password": password,
            "udp": True,
        },
    )


def parse_vmess(line: str) -> Node | None:
    payload = line[8:]
    try:
        decoded = b64decode_any(payload).decode("utf-8")
        data = json.loads(decoded)
        port = int(data["port"])
    except (ValueError, KeyError, TypeError, json.JSONDecodeError, UnicodeDecodeError):
        return None

    name = str(data.get("ps") or f"vmess@{data.get('add', '')}:{port}")
    node_data: dict[str, object] = {
        "name": name,
        "type": "vmess",
        "server": str(data["add"]),
        "port": port,
        "uuid": str(data["id"]),
        "alterId": int(str(data.get("aid", "0")) or "0"),
        "cipher": "auto",
        "udp": True,
    }
    network = str(data.get("net") or "tcp")
    if network != "tcp":
        node_data["network"] = network
    tls_enabled = str(data.get("tls", "")).lower() in {"tls", "true", "1"}
    if tls_enabled:
        node_data["tls"] = True
    path = str(data.get("path") or "")
    host = str(data.get("host") or "")
    if network == "ws":
        ws_opts: dict[str, object] = {}
        if path:
            ws_opts["path"] = path
        if host:
            ws_opts["headers"] = {"Host": host}
        if ws_opts:
            node_data["ws-opts"] = ws_opts
    return Node(name=name, data=node_data)


def parse_node(line: str) -> Node | None:
    if line.startswith("ss://"):
        return parse_ss(line)
    if line.startswith("vmess://"):
        return parse_vmess(line)
    return None

from __future__ import annotations

from pathlib import Path

import yaml

from config.schema import AppConfig


class ConfigError(ValueError):
    pass


def _require_mapping(value: object, path: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ConfigError(f"配置项必须是对象: {path}")
    return value


def load_config(path: str) -> AppConfig:
    try:
        data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    except OSError as exc:
        raise ConfigError(f"读取配置失败: {exc}") from exc
    except yaml.YAMLError as exc:
        raise ConfigError(f"解析 YAML 失败: {exc}") from exc

    root = _require_mapping(data, "root")
    required = ["subscription", "output", "server", "clash", "logging"]
    for key in required:
        if key not in root:
            raise ConfigError(f"缺少配置项: {key}")

    return AppConfig.from_dict(root)

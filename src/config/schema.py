from __future__ import annotations

from dataclasses import dataclass


def _require_mapping(value: object, path: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ValueError(f"配置项必须是对象: {path}")
    return value


def _as_int(value: object, path: str) -> int:
    if not isinstance(value, (int, float, str, bytes, bytearray)):
        raise ValueError(f"配置项必须是整数: {path}")
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"配置项必须是整数: {path}") from exc


@dataclass(slots=True)
class SubscriptionConfig:
    url: str
    timeout: int


@dataclass(slots=True)
class OutputConfig:
    path: str


@dataclass(slots=True)
class ServerConfig:
    listen: str
    port: int
    refresh_interval: int


@dataclass(slots=True)
class ClashConfig:
    port: int
    allow_lan: bool


@dataclass(slots=True)
class RotateConfig:
    type: str
    max_bytes: int
    backup_count: int


@dataclass(slots=True)
class FileLogConfig:
    enabled: bool
    path: str
    rotate: RotateConfig


@dataclass(slots=True)
class LoggingConfig:
    level: str
    format: str
    stdout: bool
    color: bool
    access_log: bool
    file: FileLogConfig


@dataclass(slots=True)
class AppConfig:
    subscription: SubscriptionConfig
    output: OutputConfig
    server: ServerConfig
    clash: ClashConfig
    logging: LoggingConfig

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> AppConfig:
        subscription = _require_mapping(data["subscription"], "subscription")
        output = _require_mapping(data["output"], "output")
        server = _require_mapping(data["server"], "server")
        clash = _require_mapping(data["clash"], "clash")
        logging_cfg = _require_mapping(data["logging"], "logging")
        file_cfg = _require_mapping(logging_cfg["file"], "logging.file")
        rotate_cfg = _require_mapping(file_cfg["rotate"], "logging.file.rotate")
        return cls(
            subscription=SubscriptionConfig(
                url=str(subscription["url"]),
                timeout=_as_int(subscription["timeout"], "subscription.timeout"),
            ),
            output=OutputConfig(path=str(output["path"])),
            server=ServerConfig(
                listen=str(server["listen"]),
                port=_as_int(server["port"], "server.port"),
                refresh_interval=_as_int(server["refresh_interval"], "server.refresh_interval"),
            ),
            clash=ClashConfig(
                port=_as_int(clash["port"], "clash.port"),
                allow_lan=bool(clash["allow_lan"]),
            ),
            logging=LoggingConfig(
                level=str(logging_cfg["level"]),
                format=str(logging_cfg["format"]),
                stdout=bool(logging_cfg["stdout"]),
                color=bool(logging_cfg["color"]),
                access_log=bool(logging_cfg["access_log"]),
                file=FileLogConfig(
                    enabled=bool(file_cfg["enabled"]),
                    path=str(file_cfg["path"]),
                    rotate=RotateConfig(
                        type=str(rotate_cfg["type"]),
                        max_bytes=_as_int(rotate_cfg["max_bytes"], "logging.file.rotate.max_bytes"),
                        backup_count=_as_int(
                            rotate_cfg["backup_count"], "logging.file.rotate.backup_count"
                        ),
                    ),
                ),
            ),
        )

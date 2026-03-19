from __future__ import annotations

from dataclasses import dataclass


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
    def from_dict(cls, data: dict[str, object]) -> "AppConfig":
        subscription = data["subscription"]
        output = data["output"]
        server = data["server"]
        clash = data["clash"]
        logging_cfg = data["logging"]
        file_cfg = logging_cfg["file"]
        rotate_cfg = file_cfg["rotate"]
        return cls(
            subscription=SubscriptionConfig(
                url=str(subscription["url"]),
                timeout=int(subscription["timeout"]),
            ),
            output=OutputConfig(path=str(output["path"])),
            server=ServerConfig(
                listen=str(server["listen"]),
                port=int(server["port"]),
                refresh_interval=int(server["refresh_interval"]),
            ),
            clash=ClashConfig(
                port=int(clash["port"]),
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
                        max_bytes=int(rotate_cfg["max_bytes"]),
                        backup_count=int(rotate_cfg["backup_count"]),
                    ),
                ),
            ),
        )

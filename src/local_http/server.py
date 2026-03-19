from __future__ import annotations

import logging
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from service.state import ServiceState


class LocalHTTPServer:
    def __init__(
        self,
        state: "ServiceState",
        *,
        listen: str,
        port: int,
        bind_server: bool = True,
        access_log: bool = True,
    ) -> None:
        self._state = state
        self.listen = listen
        self.port = port
        self.access_log = access_log
        self._logger = logging.getLogger(__name__)
        self._httpd: ThreadingHTTPServer | None = None
        if bind_server:
            self._bind()

    def _bind(self) -> None:
        server = self

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self) -> None:  # noqa: N802
                status, headers, body = server.build_response(self.path)
                self.send_response(status)
                for key, value in headers.items():
                    self.send_header(key, value)
                self.end_headers()
                if body:
                    self.wfile.write(body)
                if server.access_log:
                    server._logger.info("access path=%s status=%s", self.path, status)

            def log_message(self, format: str, *args: object) -> None:
                return

        self._httpd = ThreadingHTTPServer((self.listen, self.port), Handler)
        self.port = int(self._httpd.server_address[1])

    def build_response(self, path: str) -> tuple[int, dict[str, str], bytes]:
        if path != "/clash.yaml":
            return 404, {}, b""
        snapshot = self._state.snapshot()
        if snapshot.ready:
            body = snapshot.yaml_text.encode("utf-8")
            return 200, self._text_headers("text/yaml; charset=utf-8", body), body
        body_text = snapshot.error or "未就绪"
        body = body_text.encode("utf-8")
        return 503, self._text_headers("text/plain; charset=utf-8", body), body

    @staticmethod
    def _text_headers(content_type: str, body: bytes) -> dict[str, str]:
        return {
            "Content-Type": content_type,
            "Content-Length": str(len(body)),
        }

    def start(self) -> None:
        if self._httpd is None:
            self._bind()
        self._logger.info("本地 HTTP 服务已启动 listen=%s port=%s", self.listen, self.port)
        assert self._httpd is not None
        self._httpd.serve_forever(poll_interval=0.2)

    def stop(self) -> None:
        if self._httpd is not None:
            self._httpd.shutdown()
            self._httpd.server_close()
            self._httpd = None
        self._logger.info("本地 HTTP 服务已停止")

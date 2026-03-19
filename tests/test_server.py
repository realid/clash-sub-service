from __future__ import annotations

import unittest

from local_http.server import LocalHTTPServer
from service.state import ServiceState


class LocalHTTPServerTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.state = ServiceState()
        self.server = LocalHTTPServer(
            self.state,
            listen="127.0.0.1",
            port=0,
            bind_server=False,
        )

    def test_get_clash_yaml_returns_503_when_not_ready(self) -> None:
        status, headers, body = self.server.build_response("/clash.yaml")

        self.assertEqual(status, 503)
        self.assertEqual(headers["Content-Type"], "text/plain; charset=utf-8")
        self.assertEqual(body.decode("utf-8"), "未就绪")

    def test_get_clash_yaml_returns_200_when_ready(self) -> None:
        self.state.update_success("port: 1082\n", 1)

        status, headers, body = self.server.build_response("/clash.yaml")

        self.assertEqual(status, 200)
        self.assertEqual(body.decode("utf-8"), "port: 1082\n")
        self.assertEqual(headers["Content-Type"], "text/yaml; charset=utf-8")
        self.assertEqual(headers["Content-Length"], str(len(body)))

    def test_non_clash_yaml_path_returns_404(self) -> None:
        self.state.update_success("port: 1082\n", 1)

        status, headers, body = self.server.build_response("/config.yaml")

        self.assertEqual(status, 404)
        self.assertEqual(headers, {})
        self.assertEqual(body, b"")

    def test_get_clash_yaml_returns_error_body(self) -> None:
        self.state.update_error("refresh failed")

        status, headers, body = self.server.build_response("/clash.yaml")

        self.assertEqual(status, 503)
        self.assertEqual(headers["Content-Type"], "text/plain; charset=utf-8")
        self.assertEqual(body.decode("utf-8"), "refresh failed")


if __name__ == "__main__":
    unittest.main()

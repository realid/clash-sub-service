from __future__ import annotations

import unittest
from unittest.mock import Mock, patch

import requests

from core.fetcher import FetchError, fetch_subscription_text


class FetcherTestCase(unittest.TestCase):
    @patch("core.fetcher.requests.Session.get")
    def test_fetch_subscription_text_success(self, mock_get: Mock) -> None:
        response = Mock()
        response.ok = True
        response.status_code = 200
        response.text = "dm1lc3M6Ly90ZXN0"
        mock_get.return_value = response

        body = fetch_subscription_text("http://127.0.0.1/subscription", timeout=3)

        self.assertEqual(body, "dm1lc3M6Ly90ZXN0")
        mock_get.assert_called_once()

    @patch("core.fetcher.requests.Session.get")
    def test_fetch_subscription_text_rejects_empty_body(self, mock_get: Mock) -> None:
        response = Mock()
        response.ok = True
        response.status_code = 200
        response.text = "   "
        mock_get.return_value = response

        with self.assertRaises(FetchError) as ctx:
            fetch_subscription_text("http://127.0.0.1/subscription", timeout=3)

        self.assertIn("订阅内容为空", str(ctx.exception))

    @patch("core.fetcher.requests.Session.get")
    def test_fetch_subscription_text_rejects_http_error(self, mock_get: Mock) -> None:
        response = Mock()
        response.ok = False
        response.status_code = 503
        response.text = "upstream unavailable"
        mock_get.return_value = response

        with self.assertRaises(FetchError) as ctx:
            fetch_subscription_text("http://127.0.0.1/subscription", timeout=3)

        self.assertIn("HTTP 状态异常：503", str(ctx.exception))

    @patch("core.fetcher.requests.Session.get")
    def test_fetch_subscription_text_wraps_request_exception(self, mock_get: Mock) -> None:
        mock_get.side_effect = requests.RequestException("connection refused")

        with self.assertRaises(FetchError) as ctx:
            fetch_subscription_text("http://127.0.0.1/subscription", timeout=3)

        self.assertIn("请求失败", str(ctx.exception))

    @patch("core.fetcher.requests.Session.get")
    def test_fetch_subscription_text_tls_eof_retries_with_tls12(self, mock_get: Mock) -> None:
        response = Mock()
        response.ok = True
        response.status_code = 200
        response.text = "dm1lc3M6Ly90ZXN0"
        mock_get.side_effect = [
            requests.exceptions.SSLError(
                "[SSL: UNEXPECTED_EOF_WHILE_READING] EOF occurred in violation of protocol"
            ),
            response,
        ]

        body = fetch_subscription_text("https://example.invalid/subscription", timeout=3)

        self.assertEqual(body, "dm1lc3M6Ly90ZXN0")
        self.assertEqual(mock_get.call_count, 2)


if __name__ == "__main__":
    unittest.main()

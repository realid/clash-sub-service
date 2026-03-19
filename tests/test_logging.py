from __future__ import annotations

import unittest

from app_logging.filters import sanitize_url


class LoggingFilterTestCase(unittest.TestCase):
    def test_sanitize_url_masks_service_and_id(self) -> None:
        url = "https://example.com/subscription?service=624192&id=abc-123&token=secret"

        sanitized = sanitize_url(url)

        self.assertIn("service=%2A%2A%2A", sanitized)
        self.assertIn("id=%2A%2A%2A", sanitized)
        self.assertIn("token=%2A%2A%2A", sanitized)


if __name__ == "__main__":
    unittest.main()

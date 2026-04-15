from __future__ import annotations

import logging
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

SENSITIVE_FIELDS = {"token", "key", "password", "secret", "service", "id", "uuid", "sid"}


def sanitize_url(url: str) -> str:
    parts = urlsplit(url)
    if not parts.query:
        return url
    query = []
    for key, value in parse_qsl(parts.query, keep_blank_values=True):
        query.append((key, "***" if key.lower() in SENSITIVE_FIELDS else value))
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment))


class SensitiveURLFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            record.msg = sanitize_url(record.msg)
        if record.args:
            record.args = tuple(
                sanitize_url(arg) if isinstance(arg, str) else arg for arg in record.args
            )
        return True

from __future__ import annotations

import ssl

import requests
from requests.adapters import HTTPAdapter

DEFAULT_USER_AGENT = "clash-sub-service/0.1.1"


class FetchError(RuntimeError):
    pass


class TLS12HttpAdapter(HTTPAdapter):
    def init_poolmanager(self, *args: object, **kwargs: object) -> None:
        ssl_context = ssl.create_default_context()
        ssl_context.minimum_version = ssl.TLSVersion.TLSv1_2
        ssl_context.maximum_version = ssl.TLSVersion.TLSv1_2
        kwargs["ssl_context"] = ssl_context
        super().init_poolmanager(*args, **kwargs)


def _new_session(force_tls12: bool = False) -> requests.Session:
    session = requests.Session()
    if force_tls12:
        adapter = TLS12HttpAdapter()
        session.mount("https://", adapter)
    return session


def _is_tls_compat_error(exc: Exception) -> bool:
    text = str(exc)
    patterns = (
        "UNEXPECTED_EOF_WHILE_READING",
        "EOF occurred in violation of protocol",
        "SSLEOFError",
    )
    return any(pattern in text for pattern in patterns)


def _fetch_once(url: str, timeout: int, force_tls12: bool = False) -> requests.Response:
    session = _new_session(force_tls12=force_tls12)
    return session.get(
        url,
        timeout=timeout,
        headers={
            "User-Agent": DEFAULT_USER_AGENT,
            "Connection": "close",
        },
    )


def fetch_subscription_text(url: str, timeout: int = 15) -> str:
    try:
        response = _fetch_once(url=url, timeout=timeout, force_tls12=False)
    except requests.exceptions.SSLError as exc:
        if _is_tls_compat_error(exc):
            try:
                response = _fetch_once(url=url, timeout=timeout, force_tls12=True)
            except requests.RequestException as retry_exc:
                raise FetchError("请求失败: TLS 兼容重试后仍失败") from retry_exc
        else:
            raise FetchError("请求失败: TLS 握手异常") from exc
    except requests.RequestException as exc:
        raise FetchError("请求失败: 网络连接异常") from exc

    if not response.ok:
        raise FetchError(f"HTTP 状态异常：{response.status_code}")

    body = response.text.strip()
    if not body:
        raise FetchError("订阅内容为空")
    return body

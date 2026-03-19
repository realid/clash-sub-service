from __future__ import annotations

import requests

DEFAULT_USER_AGENT = "clash-sub-service/0.1.0"


class FetchError(RuntimeError):
    pass


def fetch_subscription_text(url: str, timeout: int = 15) -> str:
    session = requests.Session()
    try:
        response = session.get(
            url,
            timeout=timeout,
            headers={"User-Agent": DEFAULT_USER_AGENT},
        )
    except requests.RequestException as exc:
        raise FetchError(f"请求失败: {exc}") from exc

    if not response.ok:
        raise FetchError(f"HTTP 状态异常：{response.status_code}")

    body = response.text.strip()
    if not body:
        raise FetchError("订阅内容为空")
    return body

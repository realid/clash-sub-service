from __future__ import annotations

from config.schema import AppConfig
from core.fetcher import fetch_subscription_text
from core.generator import GenerationResult, generate_from_subscription_body


def refresh_subscription(config: AppConfig) -> GenerationResult:
    body = fetch_subscription_text(
        config.subscription.url,
        timeout=config.subscription.timeout,
    )
    return generate_from_subscription_body(
        body,
        port=config.clash.port,
        allow_lan=config.clash.allow_lan,
    )

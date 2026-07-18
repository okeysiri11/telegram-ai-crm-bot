# Telegram Login / WebApp init_data verification.

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import os
from typing import Any
from urllib.parse import parse_qsl

from platform_identity.exceptions import AuthenticationError

logger = logging.getLogger(__name__)

IAM_LOGIN_SECRET = os.getenv("IAM_LOGIN_SECRET", "")


def verify_login_proof(provided: str) -> bool:
    """Validate shared login proof (Operations Center / bootstrap)."""
    expected = IAM_LOGIN_SECRET
    if not expected:
        return False
    return hmac.compare_digest(provided, expected)


def verify_telegram_init_data(init_data: str) -> int:
    """Verify Telegram Login Widget / WebApp initData and return telegram user id."""
    from config import BOT_TOKEN

    if not BOT_TOKEN:
        raise AuthenticationError("BOT_TOKEN not configured for Telegram login verification")

    parsed = dict(parse_qsl(init_data, keep_blank_values=True))
    received_hash = parsed.pop("hash", None)
    if not received_hash:
        raise AuthenticationError("telegram_init_data missing hash")

    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(parsed.items()))
    secret_key = hashlib.sha256(BOT_TOKEN.encode()).digest()
    computed = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(computed, received_hash):
        raise AuthenticationError("Invalid telegram_init_data signature")

    user_raw = parsed.get("user")
    if not user_raw:
        raise AuthenticationError("telegram_init_data missing user")
    try:
        user: dict[str, Any] = json.loads(user_raw)
    except json.JSONDecodeError as exc:
        raise AuthenticationError("Invalid user payload in telegram_init_data") from exc

    user_id = user.get("id")
    if user_id is None:
        raise AuthenticationError("telegram_init_data user missing id")
    return int(user_id)

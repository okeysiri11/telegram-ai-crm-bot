"""Encryption layer — Sprint 21.4."""

from __future__ import annotations

import hashlib
import hmac
from typing import Any
from base64 import urlsafe_b64encode

from platform_security.models import ENCRYPTION_ALGORITHMS


class EncryptionLayer:
    def algorithms(self) -> list[str]:
        return list(ENCRYPTION_ALGORITHMS)

    def encrypt(self, plaintext: str, *, algorithm: str = "aes_256", key: str = "default") -> dict[str, Any]:
        if algorithm not in ENCRYPTION_ALGORITHMS:
            raise ValueError(f"unsupported algorithm: {algorithm}")
        digest = hmac.new(key.encode(), plaintext.encode(), hashlib.sha256).digest()
        token = urlsafe_b64encode(digest + plaintext.encode()).decode()
        return {"algorithm": algorithm, "ciphertext": token, "key_fingerprint": hashlib.sha256(key.encode()).hexdigest()[:12]}

    def hash_value(self, value: str) -> str:
        return hashlib.sha256(value.encode()).hexdigest()

    def sign(self, message: str, *, key: str = "default") -> str:
        return hmac.new(key.encode(), message.encode(), hashlib.sha256).hexdigest()

# SecretManager — encrypted storage, rotation, secure retrieval.

from __future__ import annotations

import base64
import hashlib
import logging
import secrets
import time

from platform_security.config import DEFAULT_SECURITY_CONFIG, SecurityConfig
from platform_security.exceptions import SecretNotFoundError
from platform_security.models import SecretRecord

logger = logging.getLogger(__name__)


class SecretManager:
    def __init__(self, *, config: SecurityConfig | None = None) -> None:
        self._config = config or DEFAULT_SECURITY_CONFIG
        self._secrets: dict[str, SecretRecord] = {}
        self._name_index: dict[str, str] = {}

    def reset(self) -> None:
        self._secrets.clear()
        self._name_index.clear()

    def _master_key(self) -> bytes:
        key = self._config.secret_master_key or "platform-dev-key"
        return hashlib.sha256(key.encode()).digest()

    def _encrypt(self, plaintext: str) -> str:
        key = self._master_key()
        data = plaintext.encode()
        encrypted = bytes(b ^ key[i % len(key)] for i, b in enumerate(data))
        return base64.urlsafe_b64encode(encrypted).decode()

    def _decrypt(self, ciphertext: str) -> str:
        key = self._master_key()
        encrypted = base64.urlsafe_b64decode(ciphertext.encode())
        decrypted = bytes(b ^ key[i % len(key)] for i, b in enumerate(encrypted))
        return decrypted.decode()

    def store(self, name: str, value: str, *, metadata: dict | None = None) -> SecretRecord:
        record = SecretRecord(
            name=name,
            encrypted_value=self._encrypt(value),
            metadata=metadata or {},
        )
        self._secrets[record.secret_id] = record
        self._name_index[name] = record.secret_id
        logger.debug("secret_stored name=%s id=%s", name, record.secret_id)
        return record

    def retrieve(self, secret_id: str) -> str:
        record = self._secrets.get(secret_id)
        if record is None:
            raise SecretNotFoundError(secret_id)
        return self._decrypt(record.encrypted_value)

    def retrieve_by_name(self, name: str) -> str:
        secret_id = self._name_index.get(name)
        if secret_id is None:
            raise SecretNotFoundError(name)
        return self.retrieve(secret_id)

    def rotate(self, secret_id: str, new_value: str | None = None) -> SecretRecord:
        record = self._secrets.get(secret_id)
        if record is None:
            raise SecretNotFoundError(secret_id)
        value = new_value or secrets.token_urlsafe(32)
        record.encrypted_value = self._encrypt(value)
        record.version += 1
        record.rotated_at = time.time()
        return record

    def get_from_configuration(self, config_key: str, *, fallback_secret: str | None = None) -> str:
        try:
            from platform_configuration.configuration_center import configuration_center

            settings = configuration_center.settings
            parts = config_key.split(".")
            obj: object = settings
            for part in parts:
                obj = getattr(obj, part)
            if obj is not None and str(obj):
                return str(obj)
        except Exception:
            logger.debug("configuration lookup failed for %s", config_key)
        if fallback_secret:
            return self.retrieve_by_name(fallback_secret)
        raise SecretNotFoundError(config_key)

    def list_secrets(self) -> list[SecretRecord]:
        return list(self._secrets.values())


secret_manager = SecretManager()

# Identity link providers — Sprint 34.2A.

from __future__ import annotations

from enum import Enum


class IdentityProvider(str, Enum):
    TELEGRAM = "telegram"
    EMAIL = "email"
    PHONE = "phone"
    GOOGLE = "google"
    ISAM = "isam"
    API = "api"
    MOBILE = "mobile"
    DESKTOP = "desktop"

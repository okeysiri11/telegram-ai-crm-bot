# Shared state for payment screenshot upload flow.

from __future__ import annotations

import uuid

pending_payment_upload: dict[int, uuid.UUID] = {}

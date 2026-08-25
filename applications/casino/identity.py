"""Non-sensitive display identities for casino presence.

Never emit emails, account ids, tokens, or raw player keys to clients.
"""

from __future__ import annotations

import hashlib


def display_identity(player_id: str) -> str:
    digest = hashlib.sha256(f"casino-display:{player_id}".encode("utf-8")).hexdigest()
    number = 100 + (int(digest[:8], 16) % 900)
    return f"Player {number}"

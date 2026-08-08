"""Telegram AI Super App — Sprint 43.3 Production UX.

Owner-first Telegram shell. Generation goes only through UnifiedAiPipeline.
Technical providers/runtime stay hidden from end users.
"""

from services.telegram_ai_super_app.service import TelegramAiSuperApp, telegram_ai_super_app

__all__ = ["TelegramAiSuperApp", "telegram_ai_super_app"]

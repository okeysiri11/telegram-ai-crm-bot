"""AI Marketing Operating System — Beauty Edition — Sprint 22.5 / v6.6.0.

Design target: src/modules/ai-marketing-os (import path platform_ai_marketing_os).
AI proposes marketing actions; owner must approve. AI never publishes alone.
"""

from platform_ai_marketing_os.facade import AIMarketingOSLibrary, ai_marketing_os_library

__all__ = ["AIMarketingOSLibrary", "ai_marketing_os_library"]

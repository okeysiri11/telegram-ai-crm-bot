"""Enterprise AI Business Advisor — Sprint 22.1 / v6.2.0.

Design target: src/modules/ai-business-advisor (import path platform_ai_business_advisor).
AI analyzes, forecasts, and recommends only — never executes commercially significant actions.
"""

from platform_ai_business_advisor.facade import AIBusinessAdvisorLibrary, ai_business_advisor_library

__all__ = ["AIBusinessAdvisorLibrary", "ai_business_advisor_library"]

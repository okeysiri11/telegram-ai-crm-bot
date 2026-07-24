"""Beauty Client Journey & Smart Booking — Sprint 22.4 / v6.5.0.

Design target: src/modules/beauty-client-journey (import path platform_beauty_client_journey).
Intelligent booking lifecycle over Beauty OS / Workspace. AI recommends only.
"""

from platform_beauty_client_journey.facade import (
    BeautyClientJourneyLibrary,
    beauty_client_journey_library,
)

__all__ = ["BeautyClientJourneyLibrary", "beauty_client_journey_library"]

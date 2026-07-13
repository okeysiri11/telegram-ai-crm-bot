# Dealer Onboarding Flow v1 tests — session lifecycle, resume, timeout, analytics.

from __future__ import annotations

import asyncio
import uuid
from datetime import timedelta

from database.models.dealer_onboarding_engine import (
    OnboardingSessionStatus,
    OnboardingStepName,
)
from database.session import get_session
from repositories.dealer_onboarding_repository import OnboardingSessionRepository
from services.pg_dealer_onboarding_engine import (
    ONBOARDING_TIMEOUT_HOURS,
    DealerOnboardingEngineV1,
)


async def run_onboarding_session_test() -> dict:
    user_id = 930_001
    session = await DealerOnboardingEngineV1.start_session(user_id)
    checks = {
        "session_created": session.get("status") == OnboardingSessionStatus.ACTIVE.value,
        "step_started": session.get("current_step") == OnboardingStepName.STARTED.value,
        "timeout_configured": ONBOARDING_TIMEOUT_HOURS == 72,
    }

    advanced = await DealerOnboardingEngineV1.advance_for_user(
        user_id,
        OnboardingStepName.AUTOMOTIVE_SELECTED.value,
        payload={"vertical": "automotive"},
    )
    checks["automotive_selected"] = (
        advanced is not None
        and advanced["current_step"] == OnboardingStepName.AUTOMOTIVE_SELECTED.value
    )

    resumed = await DealerOnboardingEngineV1.get_active_session(user_id)
    checks["resume_active"] = resumed is not None and resumed["id"] == session["id"]
    checks["resume_message"] = bool(DealerOnboardingEngineV1.resume_message(resumed or session))

    return {"ok": all(checks.values()), "checks": checks}


async def run_onboarding_timeout_test() -> dict:
    user_id = 930_002
    session = await DealerOnboardingEngineV1.start_session(user_id)
    session_id = uuid.UUID(session["id"])
    past = DealerOnboardingEngineV1._now() - timedelta(hours=ONBOARDING_TIMEOUT_HOURS + 1)

    async with get_session() as db_session:
        await OnboardingSessionRepository(db_session).update_fields(
            session_id,
            expires_at=past,
        )

    expired_count = await DealerOnboardingEngineV1.expire_stale_sessions()
    stale = await DealerOnboardingEngineV1.get_active_session(user_id)

    checks = {
        "expire_ran": expired_count >= 1,
        "no_active_after_timeout": stale is None
        or stale["status"] == OnboardingSessionStatus.EXPIRED.value,
    }
    return {"ok": all(checks.values()), "checks": checks}


async def run_onboarding_analytics_test() -> dict:
    analytics = await DealerOnboardingEngineV1.get_analytics()
    checks = {
        "has_total": "total_sessions" in analytics,
        "has_funnel": "step_funnel" in analytics,
        "has_completion_rate": "completion_rate_pct" in analytics,
        "formatted": bool(DealerOnboardingEngineV1.format_analytics(analytics)),
    }
    return {"ok": all(checks.values()), "checks": checks, "analytics": analytics}


async def run_dealer_onboarding_test_suite() -> dict:
    session_result = await run_onboarding_session_test()
    timeout_result = await run_onboarding_timeout_test()
    analytics_result = await run_onboarding_analytics_test()
    ok = (
        session_result.get("ok")
        and timeout_result.get("ok")
        and analytics_result.get("ok")
    )
    return {
        "ok": ok,
        "session": session_result,
        "timeout": timeout_result,
        "analytics": analytics_result,
    }


def run_dealer_onboarding_tests() -> dict:
    return asyncio.run(run_dealer_onboarding_test_suite())

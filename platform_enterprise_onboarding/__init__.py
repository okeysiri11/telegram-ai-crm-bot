"""Enterprise Onboarding & Data Migration — Sprint 22.9 / v6.10.0.

Design target: src/modules/enterprise-onboarding (import path platform_enterprise_onboarding).
Automated company setup from registration to go-live. AI advises only — never mutates import data.
"""

from platform_enterprise_onboarding.facade import EnterpriseOnboardingLibrary, enterprise_onboarding_library

__all__ = ["EnterpriseOnboardingLibrary", "enterprise_onboarding_library"]

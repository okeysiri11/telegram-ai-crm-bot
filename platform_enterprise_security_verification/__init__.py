"""Enterprise Security Verification — Sprint 25.5 / v8.5.0.

Design target: src/platform/security → platform_enterprise_security_verification
(CI/CD security gate before Production). Legacy ESH platform_security remains unchanged.
Verification only — no exploit payloads.
"""

from platform_enterprise_security_verification.facade import (
    SecurityVerificationLibrary,
    security_verification_library,
)

__all__ = ["SecurityVerificationLibrary", "security_verification_library"]

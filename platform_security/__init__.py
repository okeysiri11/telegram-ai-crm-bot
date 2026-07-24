"""Enterprise Security Hardening library — Sprint 21.4 / v6.0.0-rc4.

Design target: platform/security/* (import path platform_security to avoid collisions).
"""

from platform_security.facade import SecurityHardeningLibrary, security_hardening_library

__all__ = ["SecurityHardeningLibrary", "security_hardening_library"]

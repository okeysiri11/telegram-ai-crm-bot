"""Enterprise Communications Hub — Sprint 22.6 / v6.7.0.

Design target: src/modules/enterprise-communications (import path platform_communications_hub).
Universal messaging gateway — no module sends messages independently.
AI proposes only; owner approval or pre-approved automation required.
"""

from platform_communications_hub.facade import CommunicationsHubLibrary, communications_hub_library

__all__ = ["CommunicationsHubLibrary", "communications_hub_library"]

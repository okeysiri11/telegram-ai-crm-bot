"""Beauty Operating System — Sprint 22.2 / v6.3.0.

Design target: src/modules/beauty-os (import path platform_beauty_os).
Industry overlay on Enterprise Core — reuses CRM, Calendar, Finance, ABA, EPI.
"""

from platform_beauty_os.facade import BeautyOSLibrary, beauty_os_library

__all__ = ["BeautyOSLibrary", "beauty_os_library"]

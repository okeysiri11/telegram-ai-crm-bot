"""Sprint 26.6 bridge — productivity Command Center lives in command_center_platform.

Existing Sprint 20.12 ECC (executive dashboards) remains in this package.
"""

from applications.enterprise_hub.command_center_platform.facade import (
    CommandCenterPlatformSuite,
    command_center_platform,
)

# Alias for /api/enterprise-command/v1 suite
enterprise_command = command_center_platform

__all__ = ["CommandCenterPlatformSuite", "command_center_platform", "enterprise_command"]

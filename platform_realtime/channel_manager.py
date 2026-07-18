# Channel registry and role-based authorization.

from __future__ import annotations

from platform_management.permissions import ManagementRole, role_allows
from platform_realtime.exceptions import ChannelNotFoundError, RealtimePermissionError
from platform_realtime.models import ALL_CHANNELS, RealtimeChannel

_CHANNEL_MIN_ROLE: dict[str, ManagementRole] = {
    RealtimeChannel.SYSTEM.value: ManagementRole.READ_ONLY,
    RealtimeChannel.DASHBOARD.value: ManagementRole.READ_ONLY,
    RealtimeChannel.REQUESTS.value: ManagementRole.READ_ONLY,
    RealtimeChannel.WORKFLOWS.value: ManagementRole.READ_ONLY,
    RealtimeChannel.MANAGERS.value: ManagementRole.READ_ONLY,
    RealtimeChannel.AUDIT.value: ManagementRole.READ_ONLY,
    RealtimeChannel.NOTIFICATIONS.value: ManagementRole.READ_ONLY,
    RealtimeChannel.HEALTH.value: ManagementRole.READ_ONLY,
    RealtimeChannel.CONFIGURATION.value: ManagementRole.ADMINISTRATOR,
    RealtimeChannel.PLUGINS.value: ManagementRole.ADMINISTRATOR,
    RealtimeChannel.AI.value: ManagementRole.ADMINISTRATOR,
}


class ChannelManager:
    @staticmethod
    def list_channels() -> list[str]:
        return list(ALL_CHANNELS)

    @staticmethod
    def validate_channel(channel: str) -> str:
        if channel not in _CHANNEL_MIN_ROLE:
            raise ChannelNotFoundError(f"Unknown channel: {channel}")
        return channel

    @staticmethod
    def required_role(channel: str) -> ManagementRole:
        ChannelManager.validate_channel(channel)
        return _CHANNEL_MIN_ROLE[channel]

    @staticmethod
    def can_subscribe(actor_role: ManagementRole, channel: str) -> bool:
        ChannelManager.validate_channel(channel)
        return role_allows(actor_role, _CHANNEL_MIN_ROLE[channel])

    @staticmethod
    def assert_can_subscribe(actor_role: ManagementRole, channel: str) -> None:
        if not ChannelManager.can_subscribe(actor_role, channel):
            required = _CHANNEL_MIN_ROLE[channel]
            raise RealtimePermissionError(
                f"Role {actor_role.value} cannot subscribe to channel {channel} "
                f"(requires {required.value})"
            )

    @staticmethod
    def permission_matrix() -> dict[str, dict[str, bool]]:
        roles = (
            ManagementRole.READ_ONLY,
            ManagementRole.ADMINISTRATOR,
            ManagementRole.OWNER,
        )
        return {
            channel: {
                role.value: ChannelManager.can_subscribe(role, channel)
                for role in roles
            }
            for channel in ALL_CHANNELS
        }

# Channel registry — authorization delegated to IAM.

from __future__ import annotations

from platform_identity.models import Principal
from platform_identity.policy_engine import policy_engine
from platform_realtime.exceptions import ChannelNotFoundError, RealtimePermissionError
from platform_realtime.models import ALL_CHANNELS


class ChannelManager:
    @staticmethod
    def list_channels() -> list[str]:
        return list(ALL_CHANNELS)

    @staticmethod
    def validate_channel(channel: str) -> str:
        from platform_identity.permission_service import REALTIME_CHANNEL_PERMISSIONS

        if channel not in REALTIME_CHANNEL_PERMISSIONS:
            raise ChannelNotFoundError(f"Unknown channel: {channel}")
        return channel

    @staticmethod
    async def can_subscribe(principal: Principal, channel: str) -> bool:
        ChannelManager.validate_channel(channel)
        return await policy_engine.authorize_realtime_channel(principal, channel)

    @staticmethod
    async def assert_can_subscribe(principal: Principal, channel: str) -> None:
        if not await ChannelManager.can_subscribe(principal, channel):
            from platform_identity.permission_service import permission_service

            perm = permission_service.channel_permission(channel)
            raise RealtimePermissionError(
                f"Principal {principal.principal_id} cannot subscribe to channel {channel} "
                f"(requires {perm})"
            )

    @staticmethod
    def permission_matrix() -> dict[str, dict[str, bool]]:
        return policy_engine.permission_matrix()

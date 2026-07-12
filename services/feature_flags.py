# Feature flags for gradual rollout and Web UI preparation.


class FeatureFlagService:
    @staticmethod
    def is_feature_enabled(feature_name: str) -> bool:
        try:
            import asyncio

            from services.pg_feature_flag_engine import FeatureFlagEngineV1

            return asyncio.get_event_loop().run_until_complete(
                FeatureFlagEngineV1.is_enabled(flag_key=feature_name)
            )
        except Exception:
            from database import is_feature_enabled
            return is_feature_enabled(feature_name)

    @staticmethod
    def set_flag(feature_name: str, enabled: bool, description: str = None) -> bool:
        try:
            import asyncio

            from config import OWNER_ID
            from services.pg_feature_flag_engine import FeatureFlagEngineV1

            async def _update() -> None:
                try:
                    await FeatureFlagEngineV1.update_flag(
                        actor_id=OWNER_ID,
                        flag_key=feature_name,
                        enabled=enabled,
                        description=description,
                    )
                except Exception:
                    await FeatureFlagEngineV1.create_flag(
                        actor_id=OWNER_ID,
                        flag_key=feature_name,
                        name=feature_name,
                        description=description,
                        enabled=enabled,
                        rollout_percentage=100 if enabled else 0,
                    )

            asyncio.get_event_loop().run_until_complete(_update())
            return True
        except Exception:
            from database import set_feature_flag
            return set_feature_flag(feature_name, enabled, description)

    @staticmethod
    def list_flags() -> list:
        try:
            import asyncio

            from config import OWNER_ID
            from services.pg_feature_flag_engine import FeatureFlagEngineV1

            flags = asyncio.get_event_loop().run_until_complete(
                FeatureFlagEngineV1.list_flags(actor_id=OWNER_ID)
            )
            return [
                (
                    row["flag_key"],
                    row["enabled"],
                    row["description"],
                    row["updated_at"],
                )
                for row in flags
            ]
        except Exception:
            from database import cursor
            cursor.execute(
                "SELECT feature_name, enabled, description, updated_at "
                "FROM feature_flags ORDER BY feature_name"
            )
            return cursor.fetchall()

# Feature flags for gradual rollout and Web UI preparation.


class FeatureFlagService:
    @staticmethod
    def is_feature_enabled(feature_name: str) -> bool:
        from database import is_feature_enabled
        return is_feature_enabled(feature_name)

    @staticmethod
    def set_flag(feature_name: str, enabled: bool, description: str = None) -> bool:
        from database import set_feature_flag
        return set_feature_flag(feature_name, enabled, description)

    @staticmethod
    def list_flags() -> list:
        from database import cursor
        cursor.execute(
            "SELECT feature_name, enabled, description, updated_at FROM feature_flags ORDER BY feature_name"
        )
        return cursor.fetchall()

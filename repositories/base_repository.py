# Base repository pattern for future PostgreSQL adapters.


class BaseRepository:
    """Thin wrapper delegating to service layer (backward compatible)."""

    @staticmethod
    def _not_implemented():
        raise NotImplementedError("Override in subclass")

# Public ID system — human-readable external identifiers.


class PublicIdService:
    PREFIXES = {
        "requests": "AG",
        "agro_deals": "AG",
        "crypto_deals": "CR",
        "tasks": "TK",
        "calendar_events": "EV",
        "agro_documents": "DC",
    }

    @staticmethod
    def assign(table: str, row_id: int) -> str | None:
        from database import assign_public_id
        return assign_public_id(table, row_id)

    @staticmethod
    def get(table: str, row_id: int) -> str | None:
        from database import get_public_id
        return get_public_id(table, row_id)

    @staticmethod
    def generate(prefix: str) -> str:
        from database import _generate_public_id
        return _generate_public_id(prefix)

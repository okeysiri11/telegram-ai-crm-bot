# Domain model schemas (dict-based, PostgreSQL-ready).

ENTITY_TYPES = (
    "AGRO_REQUEST", "AGRO_DEAL", "CRYPTO_DEAL", "TASK",
    "CALENDAR_EVENT", "LEGAL_CASE", "PROJECT", "COMMENT", "DOCUMENT",
)

VISIBILITY_LEVELS = ("PRIVATE", "DEPARTMENT", "MANAGEMENT", "GLOBAL")

SOFT_DELETE_FIELDS = ("is_deleted", "deleted_at", "deleted_by")

PUBLIC_ID_PREFIXES = {
    "AG": "Agro (requests/deals)",
    "CR": "Crypto deals",
    "TK": "Tasks",
    "EV": "Calendar events",
    "DC": "Documents",
}

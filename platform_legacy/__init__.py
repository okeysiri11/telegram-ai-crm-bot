# platform_legacy — strict isolation boundary for legacy Telegram CRM.

from platform_legacy.facade import legacy
from platform_legacy.registry import legacy_registry
from platform_legacy.legacy_import_policy import scan_legacy_import_violations

__all__ = ["legacy", "legacy_registry", "scan_legacy_import_violations"]

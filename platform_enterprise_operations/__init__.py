"""Enterprise Operations Center & Pilot Release — Sprint 23.0 / v6.11.0.

Design target: src/modules/enterprise-operations-center → platform_enterprise_operations.
Platform owner ops: dashboard, tenant health, pilots, feedback→EPI, AI ops advice (propose only), owner approvals.
"""

from platform_enterprise_operations.facade import EnterpriseOperationsLibrary, enterprise_operations_library

__all__ = ["EnterpriseOperationsLibrary", "enterprise_operations_library"]

# Hierarchical RBAC — MODULE_ACCESS → ENTITY_ACCESS → ACTION_ACCESS with role inheritance.

from config import MANAGER_ID, OWNER_ID


class HierarchicalRBAC:
    @staticmethod
    def check(user_id: int, permission_code: str) -> bool:
        from database import has_rbac_permission
        return has_rbac_permission(user_id, permission_code)

    @staticmethod
    def can_module(user_id: int, module_key: str) -> bool:
        from database import LEGACY_MODULE_TO_RBAC, has_rbac_permission
        code = LEGACY_MODULE_TO_RBAC.get(module_key)
        if not code:
            return False
        return has_rbac_permission(user_id, code)

    @staticmethod
    def can_entity(user_id: int, entity_code: str) -> bool:
        return HierarchicalRBAC.check(user_id, entity_code)

    @staticmethod
    def can_action(user_id: int, action_code: str) -> bool:
        return HierarchicalRBAC.check(user_id, action_code)

    @staticmethod
    def get_grants(user_id: int) -> set[str]:
        from database import get_user_rbac_grants
        return get_user_rbac_grants(user_id)

    @staticmethod
    def get_effective_roles(user_id: int) -> set[str]:
        from database import get_user_effective_rbac_roles
        return get_user_effective_rbac_roles(user_id)

    @staticmethod
    def format_inspector(user_id: int) -> str:
        from database import format_hierarchical_rbac_text
        return format_hierarchical_rbac_text(user_id)

    @staticmethod
    def run_integration_test(user_id: int = None) -> dict:
        from database import RBAC_LEVELS, RBAC_PERMISSION_REGISTRY

        uid = user_id or OWNER_ID
        steps = {}
        try:
            grants = HierarchicalRBAC.get_grants(uid)
            roles = HierarchicalRBAC.get_effective_roles(uid)
            steps["effective_roles"] = sorted(roles)
            steps["grant_count"] = len(grants)

            checks = {
                "AUTO_CREATE_DEAL": HierarchicalRBAC.can_action(uid, "AUTO_CREATE_DEAL"),
                "AUTO_CLOSE_DEAL": HierarchicalRBAC.can_action(uid, "AUTO_CLOSE_DEAL"),
                "FINANCE_VIEW": HierarchicalRBAC.can_action(uid, "FINANCE_VIEW"),
                "FINANCE_APPROVE": HierarchicalRBAC.can_action(uid, "FINANCE_APPROVE"),
                "LEGAL_EDIT": HierarchicalRBAC.can_action(uid, "LEGAL_EDIT"),
                "AGRO_ASSIGN": HierarchicalRBAC.can_action(uid, "AGRO_ASSIGN"),
                "AUTO_MODULE": HierarchicalRBAC.can_module(uid, "automotive"),
                "AGRO_MODULE": HierarchicalRBAC.can_module(uid, "agro_trading"),
            }
            steps["checks"] = checks

            by_level = {level: 0 for level in RBAC_LEVELS}
            for code in grants:
                meta = RBAC_PERMISSION_REGISTRY.get(code)
                if meta:
                    by_level[meta["level"]] = by_level.get(meta["level"], 0) + 1
            steps["by_level"] = by_level

            inheritance_ok = all(
                HierarchicalRBAC.can_action(uid, action)
                for action in (
                    "AUTO_CREATE_DEAL", "FINANCE_VIEW", "FINANCE_APPROVE",
                    "LEGAL_EDIT", "AGRO_ASSIGN",
                )
            )
            steps["owner_full_access"] = inheritance_ok

            from database import cursor
            cursor.execute("SELECT COUNT(*) FROM rbac_permissions")
            steps["registry_size"] = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM rbac_role_grants")
            steps["role_grants"] = cursor.fetchone()[0]

            ok = (
                steps["grant_count"] > 0
                and steps["registry_size"] >= len(RBAC_PERMISSION_REGISTRY)
                and steps["role_grants"] > 0
                and inheritance_ok
                and by_level.get("MODULE_ACCESS", 0) >= 1
                and by_level.get("ENTITY_ACCESS", 0) >= 1
                and by_level.get("ACTION_ACCESS", 0) >= 1
            )
            return {"ok": ok, "status": "OK" if ok else "ERROR", "steps": steps}
        except Exception as exc:
            return {"ok": False, "status": "ERROR", "steps": steps, "error": str(exc)}

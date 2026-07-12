# PostgreSQL model integration test.

from config import OWNER_ID


class PostgresModelsTest:
    @staticmethod
    def run_integration_test() -> dict:
        steps = {}
        try:
            from database.base import Base
            from database.migration_models import load_all_models

            load_all_models()

            tables = sorted(Base.metadata.tables.keys())
            steps["table_count"] = len(tables)
            steps["tables"] = tables

            required = {
                "users", "roles", "user_roles", "permissions", "role_permissions",
                "deals", "platform_events", "ledger_entries",
                "commission_rules", "commissions", "commission_payments",
                "partners", "partner_deal_assignments", "calendar_events",
                "tasks", "notifications", "ai_agents", "audit_logs",
            }
            steps["required_present"] = sorted(required & set(tables))
            steps["missing"] = sorted(required - set(tables))

            from database.models.users import User
            from database.models.deals import Deal
            pk_types = {
                "users.id": User.__table__.c.id.type,
                "deals.id": Deal.__table__.c.id.type,
            }
            steps["uuid_pks"] = all(
                "UUID" in type(col).__name__ for col in pk_types.values()
            )

            fks = sum(len(t.foreign_keys) for t in Base.metadata.sorted_tables)
            indexes = sum(len(t.indexes) for t in Base.metadata.sorted_tables)
            steps["foreign_keys"] = fks
            steps["indexes"] = indexes

            ok = (
                steps["table_count"] >= 30
                and not steps["missing"]
                and steps["uuid_pks"]
                and fks >= 40
                and indexes >= 50
            )
            return {"ok": ok, "status": "OK" if ok else "ERROR", "steps": steps}
        except Exception as exc:
            return {"ok": False, "status": "ERROR", "steps": steps, "error": str(exc)}

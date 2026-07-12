# Calendar access control — department isolation on unified calendar_events.

from config import OWNER_ID, MANAGER_ID

CALENDAR_DEPARTMENTS = (
    "AGRO", "CRYPTO", "DRONE", "LEGAL", "BEAUTY", "CAFE", "SYSTEM",
)

CALENDAR_VISIBILITIES = (
    "PRIVATE", "DEPARTMENT", "MANAGEMENT", "GLOBAL",
)

MODULE_TO_DEPARTMENT = {
    "agro_trading": "AGRO",
    "crypto_otc": "CRYPTO",
    "drone": "DRONE",
    "law": "LEGAL",
    "cafe_beauty": "BEAUTY",
    "users": "SYSTEM",
    "calendar": "SYSTEM",
    "ai_assistant": "SYSTEM",
    "system": "SYSTEM",
    "reports": "SYSTEM",
}

ROLE_TO_DEPARTMENT = {
    "AGRO_MANAGER": "AGRO",
    "OTC_MANAGER": "CRYPTO",
    "CRYPTO_MANAGER": "CRYPTO",
    "LAWYER": "LEGAL",
    "BEAUTY_MANAGER": "BEAUTY",
    "ENGINEER": "DRONE",
    "DRONE_ENGINEER": "DRONE",
}

PERMISSION_TO_DEPARTMENT = {
    "agro_access": "AGRO",
    "crypto_access": "CRYPTO",
    "legal_access": "LEGAL",
    "drone_access": "DRONE",
    "beauty_access": "BEAUTY",
}

# Event row indices (after migration SELECT)
E_ID, E_TITLE, E_DESC, E_MODULE, E_TYPE = 0, 1, 2, 3, 4
E_CREATOR, E_OWNER = 5, 6
E_START, E_END, E_REMIND, E_STATUS = 7, 8, 9, 10
E_DEPT, E_VIS, E_ASSIGNED = 19, 20, 21


class CalendarAccessService:
    @staticmethod
    def department_from_module(module: str) -> str:
        from database import _normalize_calendar_module
        key = _normalize_calendar_module(module or "system")
        return MODULE_TO_DEPARTMENT.get(key, "SYSTEM")

    @staticmethod
    def can_see_all_company(user_id: int) -> bool:
        if user_id in (OWNER_ID, MANAGER_ID):
            return True
        from database import get_user_roles
        roles = set(get_user_roles(user_id))
        return bool(roles & {"OWNER", "SUPER_MANAGER"})

    @staticmethod
    def get_user_departments(user_id: int) -> set[str]:
        from database import get_user_roles, has_permission

        depts = set()
        for role in get_user_roles(user_id):
            dept = ROLE_TO_DEPARTMENT.get(role)
            if dept:
                depts.add(dept)
        for perm, dept in PERMISSION_TO_DEPARTMENT.items():
            if has_permission(user_id, perm):
                depts.add(dept)
        return depts

    @staticmethod
    def can_view_event(user_id: int, event_row: tuple) -> bool:
        if not event_row:
            return False
        if CalendarAccessService.can_see_all_company(user_id):
            return True

        creator = event_row[E_CREATOR]
        owner = event_row[E_OWNER]
        assigned = event_row[E_ASSIGNED] if len(event_row) > E_ASSIGNED else None
        if user_id in (creator, owner, assigned):
            return True

        visibility = (event_row[E_VIS] if len(event_row) > E_VIS else None) or "DEPARTMENT"
        if visibility == "PRIVATE":
            return False

        department = event_row[E_DEPT] if len(event_row) > E_DEPT else None
        if not department:
            department = CalendarAccessService.department_from_module(event_row[E_MODULE])

        user_depts = CalendarAccessService.get_user_departments(user_id)
        if visibility in ("DEPARTMENT", "GLOBAL") and department in user_depts:
            return True
        if visibility == "MANAGEMENT":
            from database import get_user_roles
            roles = set(get_user_roles(user_id))
            if roles & {"ADMIN", "MANAGER", "SUPER_MANAGER"}:
                return True
        return False

    @staticmethod
    def build_access_filter(user_id: int, scope: str = "my") -> tuple[str, list]:
        """
        Returns SQL fragment (AND ...) and params for calendar_events queries.
        scope: my | department | company
        """
        if scope == "company":
            if CalendarAccessService.can_see_all_company(user_id):
                return "", []
            scope = "department"

        personal = "(creator_id = ? OR owner_id = ? OR assigned_user_id = ?)"
        personal_params = [user_id, user_id, user_id]

        if scope == "my":
            return f" AND {personal}", personal_params

        depts = CalendarAccessService.get_user_departments(user_id)
        if not depts:
            return f" AND {personal}", personal_params

        placeholders = ",".join("?" * len(depts))
        dept_clause = (
            f"(visibility IN ('DEPARTMENT', 'GLOBAL') AND department IN ({placeholders}))"
        )
        return (
            f" AND ({personal} OR {dept_clause})",
            personal_params + list(depts),
        )

    @staticmethod
    def filter_events(user_id: int, events: list) -> list:
        return [e for e in events if CalendarAccessService.can_view_event(user_id, e)]

    @staticmethod
    def run_isolation_test() -> dict:
        """Verify Beauty user cannot see Agro events; Owner sees all."""
        from datetime import datetime
        from database import cursor, conn, _EVENT_SELECT, _normalize_calendar_module

        steps = {}
        try:
            ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

            def _insert_test_event(title, module, department):
                module = _normalize_calendar_module(module)
                cursor.execute(
                    """
                    INSERT INTO calendar_events (
                        title, module, creator_id, owner_id, start_time, status,
                        start_datetime, responsible_user, department, visibility, assigned_user_id
                    )
                    VALUES (?, ?, ?, ?, ?, 'PLANNED', ?, ?, ?, 'DEPARTMENT', ?)
                    """,
                    (title, module, OWNER_ID, OWNER_ID, ts, ts, OWNER_ID, department, OWNER_ID),
                )
                conn.commit()
                return cursor.lastrowid

            agro_id = _insert_test_event("[TEST] Agro isolation event", "agro_trading", "AGRO")
            beauty_id = _insert_test_event("[TEST] Beauty isolation event", "cafe_beauty", "BEAUTY")
            steps["agro_event"] = agro_id
            steps["beauty_event"] = beauty_id

            cursor.execute(f"{_EVENT_SELECT} WHERE id = ?", (agro_id,))
            agro_row = cursor.fetchone()
            cursor.execute(f"{_EVENT_SELECT} WHERE id = ?", (beauty_id,))
            beauty_row = cursor.fetchone()

            beauty_uid = 777001
            agro_uid = 777002
            super_uid = 777003

            def _roles_for(uid):
                if uid == beauty_uid:
                    return ["BEAUTY_MANAGER"]
                if uid == agro_uid:
                    return ["AGRO_MANAGER"]
                if uid == super_uid:
                    return ["SUPER_MANAGER"]
                return []

            import database as db

            orig_roles = db.get_user_roles
            orig_perm = db.has_permission

            def _mock_roles(uid):
                mapped = _roles_for(uid)
                return mapped if mapped else orig_roles(uid)

            db.get_user_roles = _mock_roles
            db.has_permission = lambda uid, perm: False
            try:
                beauty_sees_agro = CalendarAccessService.can_view_event(beauty_uid, agro_row)
                beauty_sees_beauty = CalendarAccessService.can_view_event(beauty_uid, beauty_row)
                agro_sees_beauty = CalendarAccessService.can_view_event(agro_uid, beauty_row)
                agro_sees_agro = CalendarAccessService.can_view_event(agro_uid, agro_row)
                owner_sees_all = (
                    CalendarAccessService.can_view_event(OWNER_ID, agro_row)
                    and CalendarAccessService.can_view_event(OWNER_ID, beauty_row)
                )
                super_sees_all = (
                    CalendarAccessService.can_view_event(super_uid, agro_row)
                    and CalendarAccessService.can_view_event(super_uid, beauty_row)
                )
            finally:
                db.get_user_roles = orig_roles
                db.has_permission = orig_perm

            steps.update({
                "beauty_sees_agro": beauty_sees_agro,
                "beauty_sees_beauty": beauty_sees_beauty,
                "agro_sees_beauty": agro_sees_beauty,
                "agro_sees_agro": agro_sees_agro,
                "owner_sees_all": owner_sees_all,
                "super_sees_all": super_sees_all,
            })
            ok = (
                not beauty_sees_agro
                and beauty_sees_beauty
                and not agro_sees_beauty
                and agro_sees_agro
                and owner_sees_all
                and super_sees_all
            )
            return {"ok": ok, "steps": steps, "status": "OK" if ok else "ERROR"}
        except Exception as exc:
            return {"ok": False, "steps": steps, "status": "ERROR", "error": str(exc)}

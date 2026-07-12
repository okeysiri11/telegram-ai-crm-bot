# Company Core Phase 1 — integration orchestration.


class CompanyCoreService:
    MODULE = "users"

    @staticmethod
    def run_integration_test(actor_id: int) -> dict:
        """
        Integration chain: Employee → Task → Calendar → KPI → Reports
        """
        from datetime import datetime
        from database import (
            ensure_employee_for_user,
            upsert_employee_kpi,
            format_company_hr_report,
            log_audit,
        )
        from services.tasks import TaskService
        from services.calendar_service import CalendarService

        steps = {}
        try:
            employee_id = ensure_employee_for_user(
                actor_id,
                department="ADMINISTRATION",
                role="MANAGER",
            )
            steps["employee"] = employee_id

            period = datetime.utcnow().strftime("%Y-%m")
            task_id = TaskService.create(
                task_type=TaskService.HUMAN,
                creator_id=actor_id,
                title=f"[Company Core] Integration task · emp #{employee_id}",
                description="integration_test",
                module=CompanyCoreService.MODULE,
                assigned_user_id=actor_id,
                priority="NORMAL",
            )
            steps["task"] = task_id

            event_id = CalendarService.create_event(
                creator_id=actor_id,
                title=f"[HR] Integration event · emp #{employee_id}",
                start_time=datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
                description=f"company_core_test|employee:{employee_id}",
                module=CompanyCoreService.MODULE,
                event_type="hr_meeting",
                owner_id=actor_id,
            )
            steps["calendar"] = event_id

            kpi_id = upsert_employee_kpi(
                employee_id,
                period=period,
                deals_count=1,
                revenue=1000,
                profit=100,
                tasks_completed=1 if task_id else 0,
                rating=4.5,
            )
            steps["kpi"] = kpi_id

            report = format_company_hr_report(employee_id)
            steps["report"] = report[:120]

            ok = all([
                employee_id,
                task_id,
                event_id,
                kpi_id,
                report,
            ])
            log_audit(
                actor_id,
                "company_core_integration_test",
                CompanyCoreService.MODULE,
                f"emp:{employee_id}:ok={ok}",
            )
            return {"ok": ok, "steps": steps, "status": "OK" if ok else "ERROR"}
        except Exception as exc:
            return {"ok": False, "steps": steps, "status": "ERROR", "error": str(exc)}

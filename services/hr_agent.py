# HRAgent — KPI, leave, sick leave, workload, reminders.

from datetime import datetime


class HRAgent:
    MODULE = "users"

    @staticmethod
    def analyze_kpi(employee_id: int, period: str = None) -> dict:
        from database import get_employee_kpi, get_employee

        kpi = get_employee_kpi(employee_id, period=period)
        emp = get_employee(employee_id=employee_id)
        if not kpi:
            return {"employee_id": employee_id, "status": "NO_DATA"}
        deals, revenue, profit, tasks, rating = kpi[3], kpi[4], kpi[5], kpi[6], kpi[7]
        score = 0
        if deals:
            score += min(deals * 5, 30)
        if tasks:
            score += min(tasks * 3, 30)
        if profit:
            score += min(profit / 1000, 40)
        level = "HIGH" if score >= 60 else "MEDIUM" if score >= 30 else "LOW"
        return {
            "employee_id": employee_id,
            "name": emp[1] if emp else "—",
            "period": kpi[2],
            "deals_count": deals,
            "revenue": revenue,
            "profit": profit,
            "tasks_completed": tasks,
            "rating": rating,
            "performance_score": round(score, 1),
            "level": level,
        }

    @staticmethod
    def request_leave(employee_id: int, actor_id: int, reason: str = "") -> bool:
        from database import set_employee_status, get_employee, log_audit
        from services.calendar_service import CalendarService
        from services.notifications import NotificationService

        emp = get_employee(employee_id=employee_id)
        if not emp:
            return False
        set_employee_status(employee_id, "ON_LEAVE")
        tg_id = emp[7] or actor_id
        CalendarService.create_event(
            creator_id=actor_id,
            title=f"[HR] Отпуск · {emp[1]}",
            start_time=datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            description=f"leave|employee:{employee_id}|{reason}",
            module="users",
            event_type="leave",
            owner_id=tg_id,
        )
        NotificationService.create_notification(
            user_id=tg_id,
            module=HRAgent.MODULE,
            title="Отпуск оформлен",
            message=reason or f"Сотрудник #{employee_id}",
            priority="INFO",
            event_type="hr_leave",
        )
        log_audit(actor_id, "hr_leave", HRAgent.MODULE, str(employee_id))
        return True

    @staticmethod
    def request_sick_leave(employee_id: int, actor_id: int, reason: str = "") -> bool:
        from database import set_employee_status, get_employee, log_audit
        from services.calendar_service import CalendarService
        from services.notifications import NotificationService

        emp = get_employee(employee_id=employee_id)
        if not emp:
            return False
        set_employee_status(employee_id, "SICK")
        tg_id = emp[7] or actor_id
        CalendarService.create_event(
            creator_id=actor_id,
            title=f"[HR] Больничный · {emp[1]}",
            start_time=datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            description=f"sick|employee:{employee_id}|{reason}",
            module="users",
            event_type="sick_leave",
            owner_id=tg_id,
        )
        NotificationService.create_notification(
            user_id=tg_id,
            module=HRAgent.MODULE,
            title="Больничный оформлен",
            message=reason or f"Сотрудник #{employee_id}",
            priority="WARNING",
            event_type="hr_sick",
        )
        log_audit(actor_id, "hr_sick_leave", HRAgent.MODULE, str(employee_id))
        return True

    @staticmethod
    def get_workload(department: str = None) -> dict:
        from database import get_employees, get_employee_time_tracking

        rows = get_employees(department=department, status="ACTIVE", limit=100)
        active = len(rows)
        on_leave = len(get_employees(department=department, status="ON_LEAVE", limit=100))
        sick = len(get_employees(department=department, status="SICK", limit=100))
        open_shifts = 0
        for row in rows:
            open_rows = get_employee_time_tracking(row[0], limit=1)
            if open_rows and not open_rows[0][2]:
                open_shifts += 1
        load_pct = round(open_shifts / active * 100, 1) if active else 0
        return {
            "department": department or "ALL",
            "active": active,
            "on_leave": on_leave,
            "sick": sick,
            "open_shifts": open_shifts,
            "load_pct": load_pct,
        }

    @staticmethod
    def send_reminders(actor_id: int) -> list[int]:
        from database import get_employees, register_module_notification, log_audit

        notified = []
        for row in get_employees(status="ACTIVE", limit=50):
            eid, name, _role, dept, *_rest = row
            tg_id = row[7]
            if not tg_id:
                continue
            nid = register_module_notification(
                tg_id,
                HRAgent.MODULE,
                title="HR напоминание",
                message=f"{name} · отдел {dept} · проверьте KPI и задачи",
                priority="INFO",
            )
            if nid:
                notified.append(nid)
        log_audit(actor_id, "hr_reminders", HRAgent.MODULE, str(len(notified)))
        return notified

    @staticmethod
    def format_report(employee_id: int) -> str:
        from database import format_employee_kpi_text, format_time_tracking_text, get_employee

        analysis = HRAgent.analyze_kpi(employee_id)
        emp = get_employee(employee_id=employee_id)
        dept = emp[3] if emp else None
        workload = HRAgent.get_workload(dept)
        lines = [
            "🤖 HRAgent\n",
            format_employee_kpi_text(employee_id),
            f"\n📈 Performance: {analysis.get('level', '—')} ({analysis.get('performance_score', 0)})",
            format_time_tracking_text(employee_id),
            f"\n👥 Загрузка отдела: active {workload['active']}, "
            f"смен открыто {workload['open_shifts']} ({workload['load_pct']}%)",
        ]
        return "\n".join(lines)

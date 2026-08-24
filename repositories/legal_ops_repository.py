"""Legal Ops repository — Sprint 51.0."""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.legal_ops import (
    LegalOpsActivity,
    LegalOpsAiAnalysis,
    LegalOpsCalendarMapping,
    LegalOpsEnforcement,
    LegalOpsMonitorChange,
    LegalOpsMonitorSettings,
    LegalOpsWatchlist,
    LegalOpsCalendarEvent,
    LegalOpsCase,
    LegalOpsClient,
    LegalOpsContract,
    LegalOpsDocument,
    LegalOpsFile,
    LegalOpsHearing,
    LegalOpsTask,
)


def _uuid(value: str | None) -> UUID | None:
    if not value:
        return None
    try:
        return UUID(str(value))
    except Exception:
        return None


def _parse_dt(value: Any) -> datetime | None:
    if value in (None, ""):
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
    return None


def _parse_amount(value: Any) -> Decimal | None:
    if value in (None, ""):
        return None
    try:
        return Decimal(str(value))
    except Exception:
        return None


def row_to_dict(row: Any) -> dict[str, Any]:
    out: dict[str, Any] = {"id": str(row.id)}
    for col in row.__table__.columns:
        if col.name == "id":
            continue
        val = getattr(row, col.name, None)
        if isinstance(val, datetime):
            out[col.name] = val.isoformat()
        elif isinstance(val, UUID):
            out[col.name] = str(val)
        elif isinstance(val, Decimal):
            out[col.name] = float(val)
        else:
            out[col.name] = val
    return out


class LegalOpsRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def insert_client(self, data: dict[str, Any]) -> LegalOpsClient:
        row = LegalOpsClient(
            organization_id=data.get("organization_id") or "default",
            tenant_id=data.get("tenant_id") or "default",
            name=data["name"],
            email=data.get("email"),
            phone=data.get("phone"),
            status=data.get("status") or "active",
            notes=data.get("notes"),
            payload=data.get("payload"),
            client_type=data.get("client_type") or "person",
            avatar_file_id=data.get("avatar_file_id"),
            address=data.get("address"),
            city=data.get("city"),
            country=data.get("country"),
            company=data.get("company"),
            position=data.get("position"),
            responsible=data.get("responsible"),
            source=data.get("source"),
            identity_data=data.get("identity_data"),
            tags=data.get("tags") or [],
            contacts=data.get("contacts") or [],
        )
        if data.get("id"):
            uid = _uuid(str(data["id"]))
            if uid:
                row.id = uid
        self._session.add(row)
        await self._session.flush()
        return row

    async def list_clients(self, organization_id: str, *, limit: int = 200) -> list[LegalOpsClient]:
        q = (
            select(LegalOpsClient)
            .where(LegalOpsClient.organization_id == organization_id)
            .order_by(LegalOpsClient.created_at.desc())
            .limit(limit)
        )
        return list((await self._session.execute(q)).scalars().all())

    async def insert_case(self, data: dict[str, Any]) -> LegalOpsCase:
        row = LegalOpsCase(
            organization_id=data.get("organization_id") or "default",
            tenant_id=data.get("tenant_id") or "default",
            client_id=data.get("client_id"),
            title=data["title"],
            case_number=data.get("case_number"),
            status=data.get("status") or "open",
            practice_area=data.get("practice_area"),
            responsible=data.get("responsible"),
            timeline=data.get("timeline") or [],
            payload=data.get("payload"),
            case_type=data.get("case_type"),
            court=data.get("court"),
            judge=data.get("judge"),
            notes=data.get("notes"),
            priority=data.get("priority"),
            participants=data.get("participants"),
            opened_at=_parse_dt(data.get("opened_at")),
            closed_at=_parse_dt(data.get("closed_at")),
            court_case_number=data.get("court_case_number"),
            description=data.get("description"),
            deadline_at=_parse_dt(data.get("deadline_at")),
        )
        if data.get("id"):
            uid = _uuid(str(data["id"]))
            if uid:
                row.id = uid
        self._session.add(row)
        await self._session.flush()
        return row

    async def get_case(self, organization_id: str, case_id: str) -> LegalOpsCase | None:
        uid = _uuid(case_id)
        if not uid:
            return None
        q = select(LegalOpsCase).where(LegalOpsCase.id == uid, LegalOpsCase.organization_id == organization_id)
        return (await self._session.execute(q)).scalar_one_or_none()

    async def update_case(self, row: LegalOpsCase, patch: dict[str, Any]) -> LegalOpsCase:
        for key in (
            "title",
            "status",
            "practice_area",
            "responsible",
            "timeline",
            "payload",
            "case_number",
            "client_id",
            "case_type",
            "court",
            "judge",
            "notes",
            "priority",
            "participants",
            "opened_at",
            "closed_at",
            "court_case_number",
            "description",
            "deadline_at",
            "archived_at",
            "archived_by",
            "archive_reason",
        ):
            if key in patch:
                val = patch[key]
                if key in {"opened_at", "closed_at", "deadline_at", "archived_at"} and isinstance(val, str) and val:
                    val = datetime.fromisoformat(val.replace("Z", "+00:00"))
                setattr(row, key, val)
        await self._session.flush()
        return row

    async def list_cases(self, organization_id: str, *, limit: int = 200) -> list[LegalOpsCase]:
        q = (
            select(LegalOpsCase)
            .where(LegalOpsCase.organization_id == organization_id)
            .order_by(LegalOpsCase.created_at.desc())
            .limit(limit)
        )
        return list((await self._session.execute(q)).scalars().all())

    async def insert_contract(self, data: dict[str, Any]) -> LegalOpsContract:
        row = LegalOpsContract(
            organization_id=data.get("organization_id") or "default",
            tenant_id=data.get("tenant_id") or "default",
            client_id=data.get("client_id"),
            case_id=data.get("case_id"),
            title=data["title"],
            status=data.get("status") or "draft",
            approval_status=data.get("approval_status") or "pending",
            body=data.get("body"),
            payload=data.get("payload"),
            contract_number=data.get("contract_number"),
            counterparty=data.get("counterparty"),
            responsible=data.get("responsible"),
            notes=data.get("notes"),
            signing_status=data.get("signing_status"),
            start_at=_parse_dt(data.get("start_at")),
            end_at=_parse_dt(data.get("end_at")),
            deadline_at=_parse_dt(data.get("deadline_at")),
            contract_type=data.get("contract_type"),
            amount=_parse_amount(data.get("amount")),
            currency=data.get("currency") or "RUB",
            contract_date=_parse_dt(data.get("contract_date")),
        )
        if data.get("id"):
            uid = _uuid(str(data["id"]))
            if uid:
                row.id = uid
        self._session.add(row)
        await self._session.flush()
        return row

    async def get_contract(self, organization_id: str, contract_id: str) -> LegalOpsContract | None:
        uid = _uuid(contract_id)
        if not uid:
            return None
        q = select(LegalOpsContract).where(
            LegalOpsContract.id == uid, LegalOpsContract.organization_id == organization_id
        )
        return (await self._session.execute(q)).scalar_one_or_none()

    async def update_contract(self, row: LegalOpsContract, patch: dict[str, Any]) -> LegalOpsContract:
        for key in (
            "title",
            "status",
            "approval_status",
            "body",
            "payload",
            "client_id",
            "case_id",
            "contract_number",
            "counterparty",
            "responsible",
            "start_at",
            "end_at",
            "deadline_at",
            "notes",
            "signing_status",
            "contract_type",
            "amount",
            "currency",
            "contract_date",
            "archived_at",
            "archived_by",
            "archive_reason",
        ):
            if key in patch:
                val = patch[key]
                if key in {"start_at", "end_at", "deadline_at", "contract_date", "archived_at"} and isinstance(val, str) and val:
                    val = datetime.fromisoformat(val.replace("Z", "+00:00"))
                if key == "amount":
                    val = _parse_amount(val)
                setattr(row, key, val)
        await self._session.flush()
        return row

    async def list_contracts(self, organization_id: str, *, limit: int = 200) -> list[LegalOpsContract]:
        q = (
            select(LegalOpsContract)
            .where(LegalOpsContract.organization_id == organization_id)
            .order_by(LegalOpsContract.created_at.desc())
            .limit(limit)
        )
        return list((await self._session.execute(q)).scalars().all())

    async def insert_document(self, data: dict[str, Any]) -> LegalOpsDocument:
        row = LegalOpsDocument(
            organization_id=data.get("organization_id") or "default",
            tenant_id=data.get("tenant_id") or "default",
            client_id=data.get("client_id"),
            case_id=data.get("case_id"),
            contract_id=data.get("contract_id"),
            title=data["title"],
            doc_type=data.get("doc_type"),
            storage_ref=data.get("storage_ref"),
            content_hash=data.get("content_hash"),
            status=data.get("status") or "uploaded",
            payload=data.get("payload"),
            description=data.get("description"),
            document_date=_parse_dt(data.get("document_date")),
            uploaded_by=data.get("uploaded_by"),
            tags=data.get("tags") or [],
        )
        if data.get("id"):
            uid = _uuid(str(data["id"]))
            if uid:
                row.id = uid
        self._session.add(row)
        await self._session.flush()
        return row

    async def list_documents(self, organization_id: str, *, limit: int = 200) -> list[LegalOpsDocument]:
        q = (
            select(LegalOpsDocument)
            .where(LegalOpsDocument.organization_id == organization_id)
            .order_by(LegalOpsDocument.created_at.desc())
            .limit(limit)
        )
        return list((await self._session.execute(q)).scalars().all())

    async def insert_task(self, data: dict[str, Any]) -> LegalOpsTask:
        row = LegalOpsTask(
            organization_id=data.get("organization_id") or "default",
            tenant_id=data.get("tenant_id") or "default",
            case_id=data.get("case_id"),
            title=data["title"],
            kind=data.get("kind") or "task",
            status=data.get("status") or "open",
            due_at=_parse_dt(data.get("due_at")),
            assignee=data.get("assignee"),
            payload=data.get("payload"),
            description=data.get("description"),
            client_id=data.get("client_id"),
            contract_id=data.get("contract_id"),
            priority=data.get("priority") or "normal",
            reminder_minutes=data.get("reminder_minutes"),
            completed_at=_parse_dt(data.get("completed_at")),
        )
        if data.get("id"):
            uid = _uuid(str(data["id"]))
            if uid:
                row.id = uid
        self._session.add(row)
        await self._session.flush()
        return row

    async def get_task(self, organization_id: str, task_id: str) -> LegalOpsTask | None:
        uid = _uuid(task_id)
        if not uid:
            return None
        q = select(LegalOpsTask).where(LegalOpsTask.id == uid, LegalOpsTask.organization_id == organization_id)
        return (await self._session.execute(q)).scalar_one_or_none()

    async def update_task(self, row: LegalOpsTask, patch: dict[str, Any]) -> LegalOpsTask:
        for key in (
            "title",
            "kind",
            "status",
            "due_at",
            "assignee",
            "payload",
            "case_id",
            "description",
            "client_id",
            "contract_id",
            "priority",
            "reminder_minutes",
            "completed_at",
            "archived_at",
            "archived_by",
            "archive_reason",
        ):
            if key in patch:
                val = patch[key]
                if key in {"due_at", "completed_at", "archived_at"} and isinstance(val, str) and val:
                    val = datetime.fromisoformat(val.replace("Z", "+00:00"))
                setattr(row, key, val)
        await self._session.flush()
        return row

    async def list_tasks(self, organization_id: str, *, limit: int = 200) -> list[LegalOpsTask]:
        q = (
            select(LegalOpsTask)
            .where(LegalOpsTask.organization_id == organization_id)
            .order_by(LegalOpsTask.created_at.desc())
            .limit(limit)
        )
        return list((await self._session.execute(q)).scalars().all())

    async def insert_hearing(self, data: dict[str, Any]) -> LegalOpsHearing:
        row = LegalOpsHearing(
            organization_id=data.get("organization_id") or "default",
            tenant_id=data.get("tenant_id") or "default",
            case_id=data.get("case_id"),
            title=data["title"],
            court_name=data.get("court_name"),
            scheduled_at=_parse_dt(data.get("scheduled_at")),
            status=data.get("status") or "scheduled",
            location=data.get("location"),
            payload=data.get("payload"),
            court_case_number=data.get("court_case_number"),
            judge=data.get("judge"),
            room=data.get("room"),
            hearing_format=data.get("hearing_format") or "in_person",
            video_url=data.get("video_url"),
            description=data.get("description"),
            result=data.get("result"),
            notes=data.get("notes"),
            ends_at=_parse_dt(data.get("ends_at")),
        )
        if data.get("id"):
            uid = _uuid(str(data["id"]))
            if uid:
                row.id = uid
        self._session.add(row)
        await self._session.flush()
        return row

    async def list_hearings(self, organization_id: str, *, limit: int = 200) -> list[LegalOpsHearing]:
        q = (
            select(LegalOpsHearing)
            .where(LegalOpsHearing.organization_id == organization_id)
            .order_by(LegalOpsHearing.created_at.desc())
            .limit(limit)
        )
        return list((await self._session.execute(q)).scalars().all())

    async def insert_calendar_event(self, data: dict[str, Any]) -> LegalOpsCalendarEvent:
        starts = data.get("starts_at")
        ends = data.get("ends_at")
        if isinstance(starts, str) and starts:
            starts = datetime.fromisoformat(starts.replace("Z", "+00:00"))
        if isinstance(ends, str) and ends:
            ends = datetime.fromisoformat(ends.replace("Z", "+00:00"))
        row = LegalOpsCalendarEvent(
            organization_id=data.get("organization_id") or "default",
            tenant_id=data.get("tenant_id") or "default",
            case_id=data.get("case_id"),
            hearing_id=data.get("hearing_id"),
            title=data["title"],
            starts_at=starts,
            ends_at=ends,
            dedupe_key=data.get("dedupe_key"),
            gcal_event_id=data.get("gcal_event_id"),
            sync_status=data.get("sync_status") or "local",
            payload=data.get("payload"),
            event_type=data.get("event_type") or "other",
            all_day=bool(data.get("all_day")),
            client_id=data.get("client_id"),
            contract_id=data.get("contract_id"),
            task_id=data.get("task_id"),
            responsible_user_id=data.get("responsible_user_id"),
            location=data.get("location"),
            description=data.get("description"),
            reminder_minutes=data.get("reminder_minutes"),
            source_kind=data.get("source_kind"),
            source_id=data.get("source_id"),
            external_event_id=data.get("external_event_id"),
            external_provider=data.get("external_provider"),
        )
        if data.get("id"):
            uid = _uuid(str(data["id"]))
            if uid:
                row.id = uid
        self._session.add(row)
        await self._session.flush()
        return row

    async def find_calendar_by_dedupe(self, organization_id: str, dedupe_key: str) -> LegalOpsCalendarEvent | None:
        q = select(LegalOpsCalendarEvent).where(
            LegalOpsCalendarEvent.organization_id == organization_id,
            LegalOpsCalendarEvent.dedupe_key == dedupe_key,
        )
        return (await self._session.execute(q)).scalar_one_or_none()

    async def find_calendar_by_gcal(self, organization_id: str, gcal_event_id: str) -> LegalOpsCalendarEvent | None:
        q = select(LegalOpsCalendarEvent).where(
            LegalOpsCalendarEvent.organization_id == organization_id,
            LegalOpsCalendarEvent.gcal_event_id == gcal_event_id,
        )
        return (await self._session.execute(q)).scalar_one_or_none()

    async def list_calendar(self, organization_id: str, *, limit: int = 200) -> list[LegalOpsCalendarEvent]:
        q = (
            select(LegalOpsCalendarEvent)
            .where(LegalOpsCalendarEvent.organization_id == organization_id)
            .order_by(LegalOpsCalendarEvent.created_at.desc())
            .limit(limit)
        )
        return list((await self._session.execute(q)).scalars().all())

    async def insert_activity(self, data: dict[str, Any]) -> LegalOpsActivity:
        row = LegalOpsActivity(
            organization_id=data.get("organization_id") or "default",
            tenant_id=data.get("tenant_id") or "default",
            entity_type=data["entity_type"],
            entity_id=data["entity_id"],
            action=data["action"],
            actor_role=data.get("actor_role"),
            actor_id=data.get("actor_id"),
            summary=data.get("summary"),
            payload=data.get("payload"),
        )
        if data.get("id"):
            uid = _uuid(str(data["id"]))
            if uid:
                row.id = uid
        self._session.add(row)
        await self._session.flush()
        return row

    async def list_activity(
        self,
        organization_id: str,
        *,
        entity_type: str | None = None,
        entity_id: str | None = None,
        limit: int = 200,
    ) -> list[LegalOpsActivity]:
        q = select(LegalOpsActivity).where(LegalOpsActivity.organization_id == organization_id)
        if entity_type:
            q = q.where(LegalOpsActivity.entity_type == entity_type)
        if entity_id:
            q = q.where(LegalOpsActivity.entity_id == entity_id)
        q = q.order_by(LegalOpsActivity.created_at.desc()).limit(limit)
        return list((await self._session.execute(q)).scalars().all())

    async def _get(self, model, organization_id: str, item_id: str):
        uid = _uuid(item_id)
        if not uid:
            return None
        q = select(model).where(model.id == uid, model.organization_id == organization_id)
        return (await self._session.execute(q)).scalar_one_or_none()

    async def get_client(self, organization_id: str, item_id: str) -> LegalOpsClient | None:
        return await self._get(LegalOpsClient, organization_id, item_id)

    async def get_document(self, organization_id: str, item_id: str) -> LegalOpsDocument | None:
        return await self._get(LegalOpsDocument, organization_id, item_id)

    async def get_hearing(self, organization_id: str, item_id: str) -> LegalOpsHearing | None:
        return await self._get(LegalOpsHearing, organization_id, item_id)

    async def get_calendar(self, organization_id: str, item_id: str) -> LegalOpsCalendarEvent | None:
        return await self._get(LegalOpsCalendarEvent, organization_id, item_id)

    async def get_file(self, organization_id: str, item_id: str) -> LegalOpsFile | None:
        return await self._get(LegalOpsFile, organization_id, item_id)

    async def find_calendar_by_source(
        self, organization_id: str, source_kind: str, source_id: str
    ) -> LegalOpsCalendarEvent | None:
        q = select(LegalOpsCalendarEvent).where(
            LegalOpsCalendarEvent.organization_id == organization_id,
            LegalOpsCalendarEvent.source_kind == source_kind,
            LegalOpsCalendarEvent.source_id == source_id,
        )
        return (await self._session.execute(q)).scalar_one_or_none()

    async def update_row(self, row: Any, patch: dict[str, Any], keys: tuple[str, ...]) -> Any:
        cols = {c.name for c in row.__table__.columns}
        for key in keys:
            if key not in patch or key not in cols:
                continue
            val = patch[key]
            if key.endswith("_at"):
                if val in ("", None):
                    val = None
                elif isinstance(val, str):
                    try:
                        val = datetime.fromisoformat(val.replace("Z", "+00:00"))
                    except ValueError:
                        continue
            elif key == "reminder_minutes" and val not in (None, ""):
                try:
                    val = int(val)
                except (TypeError, ValueError):
                    continue
            elif key == "all_day":
                val = bool(val) if not isinstance(val, str) else val.lower() in {"1", "true", "yes"}
            elif key in {"file_version", "size", "reminder_minutes"} and val not in (None, ""):
                try:
                    val = int(val)
                except (TypeError, ValueError):
                    continue
            elif key == "amount":
                val = _parse_amount(val)
            setattr(row, key, val)
        if "updated_at" in cols:
            setattr(row, "updated_at", datetime.now(timezone.utc))
        await self._session.flush()
        return row

    async def insert_file(self, data: dict[str, Any]) -> LegalOpsFile:
        row = LegalOpsFile(
            organization_id=data.get("organization_id") or "default",
            tenant_id=data.get("tenant_id") or "default",
            entity_type=data.get("entity_type"),
            entity_id=data.get("entity_id"),
            filename=data["filename"],
            mime_type=data.get("mime_type"),
            size=data.get("size"),
            storage_path=data["storage_path"],
            description=data.get("description"),
            file_version=int(data.get("file_version") or 1),
            uploaded_by=data.get("uploaded_by"),
            inbox_status=data.get("inbox_status") or "linked",
            payload=data.get("payload"),
        )
        if data.get("id"):
            uid = _uuid(str(data["id"]))
            if uid:
                row.id = uid
        self._session.add(row)
        await self._session.flush()
        return row

    async def list_files(
        self,
        organization_id: str,
        *,
        entity_type: str | None = None,
        entity_id: str | None = None,
        inbox_status: str | None = None,
        limit: int = 200,
    ) -> list[LegalOpsFile]:
        q = select(LegalOpsFile).where(LegalOpsFile.organization_id == organization_id)
        if entity_type:
            q = q.where(LegalOpsFile.entity_type == entity_type)
        if entity_id:
            q = q.where(LegalOpsFile.entity_id == entity_id)
        if inbox_status:
            q = q.where(LegalOpsFile.inbox_status == inbox_status)
        q = q.order_by(LegalOpsFile.created_at.desc()).limit(limit)
        return list((await self._session.execute(q)).scalars().all())

    async def insert_ai_analysis(self, data: dict[str, Any]) -> LegalOpsAiAnalysis:
        row = LegalOpsAiAnalysis(
            organization_id=data.get("organization_id") or "default",
            tenant_id=data.get("tenant_id") or "default",
            workspace_kind=data.get("workspace_kind") or "analysis",
            action=data.get("action"),
            mode=data.get("mode"),
            target_type=data.get("target_type"),
            target_id=data.get("target_id"),
            client_id=data.get("client_id"),
            case_id=data.get("case_id"),
            question=data.get("question"),
            result=data.get("result"),
            sources=data.get("sources"),
            context_snapshot=data.get("context_snapshot"),
            provider_meta=data.get("provider_meta"),
            created_tasks=data.get("created_tasks") or [],
            created_events=data.get("created_events") or [],
            created_documents=data.get("created_documents") or [],
            actor_role=data.get("actor_role"),
            actor_id=data.get("actor_id"),
            status=data.get("status") or "active",
            payload=data.get("payload"),
        )
        if data.get("id"):
            uid = _uuid(str(data["id"]))
            if uid:
                row.id = uid
        self._session.add(row)
        await self._session.flush()
        return row

    async def list_ai_analyses(self, organization_id: str, *, limit: int = 200) -> list[LegalOpsAiAnalysis]:
        q = (
            select(LegalOpsAiAnalysis)
            .where(LegalOpsAiAnalysis.organization_id == organization_id)
            .order_by(LegalOpsAiAnalysis.created_at.desc())
            .limit(limit)
        )
        return list((await self._session.execute(q)).scalars().all())

    async def get_ai_analysis(self, organization_id: str, item_id: str) -> LegalOpsAiAnalysis | None:
        uid = _uuid(item_id)
        if not uid:
            return None
        q = select(LegalOpsAiAnalysis).where(
            LegalOpsAiAnalysis.organization_id == organization_id,
            LegalOpsAiAnalysis.id == uid,
        )
        return (await self._session.execute(q)).scalar_one_or_none()

    async def insert_watchlist(self, data: dict[str, Any]) -> LegalOpsWatchlist:
        row = LegalOpsWatchlist(
            organization_id=data.get("organization_id") or "default",
            tenant_id=data.get("tenant_id") or "default",
            case_id=data.get("case_id"),
            client_id=data.get("client_id"),
            entity_kind=data.get("entity_kind") or "court_case",
            external_case_number=data.get("external_case_number"),
            provider=data.get("provider") or "manual_import",
            status=data.get("status") or "active",
            last_checked_at=_parse_dt(data.get("last_checked_at")),
            last_success_at=_parse_dt(data.get("last_success_at")),
            next_check_at=_parse_dt(data.get("next_check_at")),
            last_error=data.get("last_error"),
            fingerprint=data.get("fingerprint"),
            normalized_state=data.get("normalized_state"),
            automation=data.get("automation"),
            payload=data.get("payload"),
            title=data.get("title"),
            source_url=data.get("source_url"),
            check_frequency=data.get("check_frequency"),
            comment=data.get("comment"),
            counterparty=data.get("counterparty"),
            decision_ref=data.get("decision_ref"),
            enforcement_id=data.get("enforcement_id"),
            active=bool(data.get("active", True)),
        )
        if data.get("id"):
            uid = _uuid(str(data["id"]))
            if uid:
                row.id = uid
        self._session.add(row)
        await self._session.flush()
        return row

    async def list_watchlist(self, organization_id: str, *, limit: int = 500) -> list[LegalOpsWatchlist]:
        q = select(LegalOpsWatchlist).where(LegalOpsWatchlist.organization_id == organization_id).order_by(LegalOpsWatchlist.created_at.desc()).limit(limit)
        return list((await self._session.execute(q)).scalars().all())

    async def get_watchlist(self, organization_id: str, item_id: str) -> LegalOpsWatchlist | None:
        uid = _uuid(item_id)
        if not uid:
            return None
        q = select(LegalOpsWatchlist).where(LegalOpsWatchlist.organization_id == organization_id, LegalOpsWatchlist.id == uid)
        return (await self._session.execute(q)).scalar_one_or_none()

    async def insert_monitor_change(self, data: dict[str, Any]) -> LegalOpsMonitorChange:
        row = LegalOpsMonitorChange(
            organization_id=data.get("organization_id") or "default",
            tenant_id=data.get("tenant_id") or "default",
            watchlist_id=data.get("watchlist_id"),
            case_id=data.get("case_id"),
            client_id=data.get("client_id"),
            change_type=data["change_type"],
            title=data["title"],
            detail=data.get("detail"),
            dedupe_key=data["dedupe_key"],
            provider=data.get("provider"),
            source_label=data.get("source_label"),
            read_at=_parse_dt(data.get("read_at")),
            payload=data.get("payload"),
            workflow_status=data.get("workflow_status") or "new",
            summary=data.get("summary"),
            old_fingerprint=data.get("old_fingerprint"),
            new_fingerprint=data.get("new_fingerprint"),
            source_reference=data.get("source_reference"),
            enforcement_id=data.get("enforcement_id"),
            suggestions=data.get("suggestions"),
        )
        if data.get("id"):
            uid = _uuid(str(data["id"]))
            if uid:
                row.id = uid
        self._session.add(row)
        await self._session.flush()
        return row

    async def list_monitor_changes(self, organization_id: str, *, limit: int = 500) -> list[LegalOpsMonitorChange]:
        q = select(LegalOpsMonitorChange).where(LegalOpsMonitorChange.organization_id == organization_id).order_by(LegalOpsMonitorChange.created_at.desc()).limit(limit)
        return list((await self._session.execute(q)).scalars().all())

    async def get_monitor_change(self, organization_id: str, item_id: str) -> LegalOpsMonitorChange | None:
        uid = _uuid(item_id)
        if not uid:
            return None
        q = select(LegalOpsMonitorChange).where(LegalOpsMonitorChange.organization_id == organization_id, LegalOpsMonitorChange.id == uid)
        return (await self._session.execute(q)).scalar_one_or_none()

    async def insert_enforcement(self, data: dict[str, Any]) -> LegalOpsEnforcement:
        row = LegalOpsEnforcement(
            organization_id=data.get("organization_id") or "default",
            tenant_id=data.get("tenant_id") or "default",
            production_number=data["production_number"],
            client_id=data.get("client_id"),
            case_id=data.get("case_id"),
            debtor=data.get("debtor"),
            creditor=data.get("creditor"),
            executor=data.get("executor"),
            status=data.get("status") or "open",
            opened_at=_parse_dt(data.get("opened_at")),
            last_checked_at=_parse_dt(data.get("last_checked_at")),
            notes=data.get("notes"),
            provider=data.get("provider"),
            payload=data.get("payload"),
        )
        if data.get("id"):
            uid = _uuid(str(data["id"]))
            if uid:
                row.id = uid
        self._session.add(row)
        await self._session.flush()
        return row

    async def list_enforcement(self, organization_id: str, *, limit: int = 500) -> list[LegalOpsEnforcement]:
        q = select(LegalOpsEnforcement).where(LegalOpsEnforcement.organization_id == organization_id).order_by(LegalOpsEnforcement.created_at.desc()).limit(limit)
        return list((await self._session.execute(q)).scalars().all())

    async def get_enforcement(self, organization_id: str, item_id: str) -> LegalOpsEnforcement | None:
        uid = _uuid(item_id)
        if not uid:
            return None
        q = select(LegalOpsEnforcement).where(LegalOpsEnforcement.organization_id == organization_id, LegalOpsEnforcement.id == uid)
        return (await self._session.execute(q)).scalar_one_or_none()

    async def insert_calendar_mapping(self, data: dict[str, Any]) -> LegalOpsCalendarMapping:
        row = LegalOpsCalendarMapping(
            organization_id=data.get("organization_id") or "default",
            tenant_id=data.get("tenant_id") or "default",
            internal_event_id=data["internal_event_id"],
            provider=data.get("provider") or "google",
            external_calendar_id=data.get("external_calendar_id"),
            external_event_id=data["external_event_id"],
            sync_version=int(data.get("sync_version") or 1),
            last_synced_at=_parse_dt(data.get("last_synced_at")),
            sync_direction=data.get("sync_direction") or "ados_to_google",
            payload=data.get("payload"),
        )
        if data.get("id"):
            uid = _uuid(str(data["id"]))
            if uid:
                row.id = uid
        self._session.add(row)
        await self._session.flush()
        return row

    async def list_calendar_mappings(self, organization_id: str, *, limit: int = 500) -> list[LegalOpsCalendarMapping]:
        q = select(LegalOpsCalendarMapping).where(LegalOpsCalendarMapping.organization_id == organization_id).limit(limit)
        return list((await self._session.execute(q)).scalars().all())

    async def upsert_monitor_settings(self, data: dict[str, Any]) -> LegalOpsMonitorSettings:
        org = data.get("organization_id") or "default"
        q = select(LegalOpsMonitorSettings).where(LegalOpsMonitorSettings.organization_id == org)
        row = (await self._session.execute(q)).scalar_one_or_none()
        if row is None:
            row = LegalOpsMonitorSettings(
                organization_id=org,
                tenant_id=data.get("tenant_id") or org,
                timezone=data.get("timezone") or "Europe/Kyiv",
                cron_morning=data.get("cron_morning") or "0 9 * * *",
                cron_evening=data.get("cron_evening") or "0 18 * * *",
                google_sync=data.get("google_sync"),
                payload=data.get("payload"),
            )
            if data.get("id"):
                uid = _uuid(str(data["id"]))
                if uid:
                    row.id = uid
            self._session.add(row)
        else:
            for k in ("timezone", "cron_morning", "cron_evening", "google_sync", "payload"):
                if data.get(k) is not None:
                    setattr(row, k, data.get(k))
        await self._session.flush()
        return row

    async def get_monitor_settings(self, organization_id: str) -> LegalOpsMonitorSettings | None:
        q = select(LegalOpsMonitorSettings).where(LegalOpsMonitorSettings.organization_id == organization_id)
        return (await self._session.execute(q)).scalar_one_or_none()


"""Sprint Lawyer 3.2 — AI analysis / AI Lawyer workspace on Legal Ops."""

from __future__ import annotations

import base64
import logging
import re
import uuid
from typing import Any

from services.legal_ops import ai_workspace as aiw
from services.legal_ops.desk_ops import active_only
from services.legal_ops.rbac import require

logger = logging.getLogger(__name__)


def _normalize_date_to_iso(date: str | None) -> str | None:
    if not date:
        return None
    s = str(date).strip()
    if re.match(r"^\d{4}-\d{2}-\d{2}", s):
        return s[:10]
    m = re.match(r"^(\d{1,2})[./](\d{1,2})[./](\d{2,4})$", s)
    if m:
        d, mo, y = m.group(1), m.group(2), m.group(3)
        if len(y) == 2:
            y = "20" + y
        return f"{int(y):04d}-{int(mo):02d}-{int(d):02d}"
    return None


class LegalOpsAiMixin:
    """AI-анализ + AI-юрист — single service layer, no duplicate AI product."""

    def ai_catalog(self) -> dict[str, Any]:
        return {
            "ok": True,
            "actions": aiw.ANALYSIS_ACTIONS,
            "modes": aiw.LAWYER_MODES,
            "draft_kinds": aiw.DRAFT_KINDS,
            "doc_statuses": aiw.DOC_STATUSES,
            "concepts": {
                "ai_analysis": "Анализ конкретного объекта или документа.",
                "ai_lawyer": "Диалоговый помощник с контекстом клиента/дела/документов; создаёт черновики и планы.",
            },
        }

    def _resolve_target_text(self, org: str, body: dict[str, Any]) -> dict[str, Any]:
        bag = self._bag(org)  # type: ignore[attr-defined]
        pasted = str(body.get("text") or body.get("pasted_text") or "").strip()
        question = str(body.get("question") or body.get("prompt") or "").strip()
        target_type = str(body.get("target_type") or body.get("target") or "text").strip()
        target_id = str(body.get("target_id") or body.get("document_id") or body.get("contract_id") or "").strip() or None
        extraction: dict[str, Any] = {"ok": True, "method": "none"}
        chunks: list[str] = []

        if pasted:
            chunks.append(pasted)
            extraction = {"ok": True, "method": "pasted_text"}

        b64 = body.get("file_base64") or body.get("attachment_base64")
        filename = str(body.get("filename") or body.get("attachment_name") or "upload.txt")
        mime = body.get("mime_type")
        if b64:
            try:
                raw = base64.b64decode(str(b64), validate=False)
            except Exception:
                raw = b""
            extraction = aiw.extract_plain_text_from_bytes(filename, mime, raw)
            if extraction.get("text"):
                chunks.append(str(extraction["text"]))

        file_id = str(body.get("file_id") or "").strip()
        if file_id:
            frow = next((f for f in bag.get("files", []) if str(f.get("id")) == file_id), None)
            if frow:
                try:
                    from services.legal_ops import files as file_store

                    data = file_store.read_bytes(str(frow.get("storage_path") or ""))
                    extraction = aiw.extract_plain_text_from_bytes(
                        str(frow.get("filename") or filename),
                        frow.get("mime_type"),
                        data or b"",
                    )
                    if extraction.get("text"):
                        chunks.append(str(extraction["text"]))
                except Exception as exc:
                    logger.warning("ai file read failed: %s", exc)
                    extraction = {"ok": False, "method": "file", "message_ru": str(exc)}

        entity_text = ""
        if target_type and target_id:
            key = {
                "document": "documents",
                "contract": "contracts",
                "case": "cases",
                "client": "clients",
                "task": "tasks",
                "hearing": "hearings",
            }.get(target_type)
            if key:
                item = next((x for x in bag.get(key, []) if str(x.get("id")) == target_id), None)
                if item:
                    entity_text = " | ".join(
                        str(item.get(k) or "")
                        for k in (
                            "title",
                            "name",
                            "description",
                            "notes",
                            "summary",
                            "case_number",
                            "status",
                        )
                        if item.get(k)
                    )
                    preview = (item.get("payload") or {}).get("content_preview") if isinstance(item.get("payload"), dict) else None
                    if preview:
                        entity_text = f"{entity_text}\n{preview}"
                    chunks.append(entity_text)

        context_text = "\n\n".join(c for c in chunks if c).strip()
        return {
            "target_type": target_type,
            "target_id": target_id,
            "question": question or pasted or "Проанализируй",
            "context_text": context_text,
            "extraction": extraction,
            "client_id": body.get("client_id"),
            "case_id": body.get("case_id"),
        }

    def build_context_pack(
        self,
        organization_id: str,
        *,
        client_id: str | None = None,
        case_id: str | None = None,
        document_ids: list[str] | None = None,
        contract_id: str | None = None,
        hearing_id: str | None = None,
        change_id: str | None = None,
        exclude: list[str] | None = None,
        role: str | None = None,
    ) -> dict[str, Any]:
        denied = require(role, "ai")
        if denied:
            return denied
        org = organization_id
        # ensure_hydrated called by callers
        bag = self._bag(org)  # type: ignore[attr-defined]
        exclude_set = set(exclude or [])
        sources: list[dict[str, Any]] = []
        texts: list[str] = []

        seen_sids: set[str] = set()

        def add(kind: str, item: dict[str, Any], label: str) -> None:
            sid = f"{kind}:{item.get('id')}"
            if sid in exclude_set or sid in seen_sids:
                return
            seen_sids.add(sid)
            sources.append({"id": sid, "kind": kind, "label": label, "item_id": item.get("id"), "included": True})
            bit = " | ".join(
                str(item.get(k) or "")
                for k in ("title", "name", "description", "notes", "status", "due_at", "starts_at")
                if item.get(k)
            )
            if bit:
                texts.append(f"[{kind}] {bit}")

        # explicit anchors (Lawyer 3.6 handoff): contract / hearing / monitoring change
        change = None
        if change_id:
            change = next(
                (c for c in bag.get("monitor_changes", []) if str(c.get("id")) == str(change_id)), None
            )
            if change:
                add("monitor_change", change, f"Изменение мониторинга {change.get('summary') or change_id}")
                case_id = case_id or change.get("case_id")
                client_id = client_id or change.get("client_id")

        hearing_anchor = None
        if hearing_id:
            hearing_anchor = next(
                (h for h in active_only(bag["hearings"]) if str(h.get("id")) == str(hearing_id)), None
            )
            if hearing_anchor:
                add("hearing", hearing_anchor, f"Заседание {hearing_anchor.get('title') or hearing_id}")
                case_id = case_id or hearing_anchor.get("case_id")

        contract_anchor = None
        if contract_id:
            contract_anchor = next(
                (c for c in active_only(bag["contracts"]) if str(c.get("id")) == str(contract_id)), None
            )
            if contract_anchor:
                add("contract", contract_anchor, f"Договор {contract_anchor.get('title') or contract_id}")
                case_id = case_id or contract_anchor.get("case_id")
                client_id = client_id or contract_anchor.get("client_id")

        case = None
        if case_id:
            case = next((c for c in active_only(bag["cases"]) if str(c.get("id")) == str(case_id)), None)
            if case:
                add("case", case, f"Дело {case.get('case_number') or case.get('title') or case_id}")
                client_id = client_id or case.get("client_id")

        client = None
        if client_id:
            client = next((c for c in active_only(bag["clients"]) if str(c.get("id")) == str(client_id)), None)
            if client:
                add("client", client, f"Клиент {client.get('name') or client_id}")

        docs = active_only(bag["documents"])
        if case_id:
            docs = [d for d in docs if str(d.get("case_id") or "") == str(case_id)]
        elif client_id:
            docs = [d for d in docs if str(d.get("client_id") or "") == str(client_id)]
        if document_ids:
            want = {str(x) for x in document_ids}
            docs = [d for d in docs if str(d.get("id")) in want]
        for d in docs[:20]:
            add("document", d, f"Документ {d.get('title') or d.get('id')}")

        contracts = active_only(bag["contracts"])
        if case_id:
            contracts = [c for c in contracts if str(c.get("case_id") or "") == str(case_id)]
        elif client_id:
            contracts = [c for c in contracts if str(c.get("client_id") or "") == str(client_id)]
        for c in contracts[:10]:
            add("contract", c, f"Договор {c.get('title') or c.get('id')}")

        tasks = active_only(bag["tasks"])
        if case_id:
            tasks = [t for t in tasks if str(t.get("case_id") or "") == str(case_id)]
        elif client_id:
            tasks = [t for t in tasks if str(t.get("client_id") or "") == str(client_id)]
        for t in tasks[:15]:
            add("task", t, f"Задача {t.get('title') or t.get('id')}")

        hearings = active_only(bag["hearings"])
        if case_id:
            hearings = [h for h in hearings if str(h.get("case_id") or "") == str(case_id)]
        for h in hearings[:10]:
            add("hearing", h, f"Заседание {h.get('title') or h.get('id')}")

        analyses = active_only(bag.get("ai_analyses", []))
        if case_id:
            analyses = [a for a in analyses if str(a.get("case_id") or "") == str(case_id)]
        for a in analyses[:10]:
            add("ai_analysis", a, f"AI-анализ {a.get('action') or a.get('id')}")

        inspector = {
            "case": 1 if case else 0,
            "client": 1 if client else 0,
            "documents": sum(1 for s in sources if s["kind"] == "document"),
            "contracts": sum(1 for s in sources if s["kind"] == "contract"),
            "tasks": sum(1 for s in sources if s["kind"] == "task"),
            "hearings": sum(1 for s in sources if s["kind"] == "hearing"),
            "ai_analyses": sum(1 for s in sources if s["kind"] == "ai_analysis"),
            "monitor_changes": sum(1 for s in sources if s["kind"] == "monitor_change"),
        }
        return {
            "ok": True,
            "sources": sources,
            "inspector": inspector,
            "context_text": "\n".join(texts),
            "external_legal": {
                "connected": False,
                "note_ru": "Внешние юридические реестры не подключены в Sprint 3.2.",
            },
            "tenant_id": org,
            "organization_id": org,
        }

    async def ai_analyze(self, organization_id: str, body: dict[str, Any], role: str | None = None) -> dict[str, Any]:
        denied = require(role, "ai")
        if denied:
            return denied
        org = organization_id if organization_id else "default"
        await self.ensure_hydrated(org)  # type: ignore[attr-defined]
        resolved = self._resolve_target_text(org, body)
        action = str(body.get("action") or "summarize").strip() or "summarize"
        if action not in {a["id"] for a in aiw.ANALYSIS_ACTIONS}:
            action = "summarize"

        llm = await aiw.maybe_llm_complete(
            f"Legal analysis action={action} question={resolved['question']}\n{resolved['context_text'][:2000]}"
        )
        provider_meta = {
            "provider": llm.get("provider") or "legal_ops_deterministic",
            "model": llm.get("model") or "rules-v1",
            "mocked": True,
        }
        structured = aiw.build_structured_analysis(
            action=action,
            question=resolved["question"],
            context_text=resolved["context_text"],
            target_type=resolved["target_type"],
            target_id=resolved["target_id"],
            provider_meta=provider_meta,
        )
        if llm.get("ok") and llm.get("text"):
            structured["llm_note"] = str(llm["text"])[:500]

        if resolved["extraction"].get("needs_vision"):
            structured["missing_data"].append(resolved["extraction"].get("message_ru") or "Требуется vision/OCR")
        elif resolved["extraction"].get("ok") is False and resolved["extraction"].get("message_ru"):
            structured["missing_data"].append(resolved["extraction"]["message_ru"])

        item = {
            "id": str(uuid.uuid4()),
            "organization_id": org,
            "tenant_id": org,
            "workspace_kind": "analysis",
            "action": action,
            "mode": None,
            "target_type": resolved["target_type"],
            "target_id": resolved["target_id"],
            "client_id": body.get("client_id") or resolved.get("client_id"),
            "case_id": body.get("case_id") or resolved.get("case_id"),
            "question": resolved["question"],
            "result": structured,
            "sources": structured.get("sources"),
            "context_snapshot": {
                "extraction": resolved["extraction"],
                "context_len": len(resolved["context_text"] or ""),
            },
            "provider_meta": provider_meta,
            "created_tasks": [],
            "created_events": [],
            "created_documents": [],
            "actor_role": role,
            "actor_id": body.get("actor_id") or role,
            "status": "active",
            "payload": {"workspace": "ai_analysis"},
            "created_at": None,
        }
        saved = await self._persist("ai_analysis", item)  # type: ignore[attr-defined]
        if not saved.get("created_at"):
            from datetime import datetime, timezone

            saved["created_at"] = datetime.now(timezone.utc).isoformat()
        self._bag(org).setdefault("ai_analyses", []).insert(0, saved)  # type: ignore[attr-defined]

        await self._activity(  # type: ignore[attr-defined]
            organization_id=org,
            entity_type=resolved["target_type"] or "analysis",
            entity_id=resolved["target_id"] or saved["id"],
            action="ai_analysis_executed",
            summary=f"AI-анализ ({action}) сохранён",
            role=role,
            payload={"analysis_id": saved["id"], "action": action},
        )
        # Backward-compatible flat fields
        analysis = {
            **structured,
            "summary": structured.get("summary"),
            "recommendation": "; ".join(structured.get("recommended_actions") or [])[:300],
            "disclaimer": structured.get("disclaimer"),
            "engine": "legal_ops_ai_workspace",
            "analysis_id": saved["id"],
            "id": saved["id"],
        }
        return {"ok": True, "analysis": analysis, "item": saved}

    async def list_ai_analyses(
        self,
        organization_id: str,
        role: str | None = None,
        *,
        case_id: str | None = None,
        include_archived: bool = False,
    ) -> dict[str, Any]:
        denied = require(role, "list")
        if denied:
            return denied
        org = organization_id
        await self.ensure_hydrated(org)  # type: ignore[attr-defined]
        items = self._bag(org).get("ai_analyses", [])  # type: ignore[attr-defined]
        if not include_archived:
            items = active_only(items)
        if case_id:
            items = [a for a in items if str(a.get("case_id") or "") == str(case_id)]
        return {"ok": True, "items": items}

    async def get_ai_analysis(self, organization_id: str, analysis_id: str, role: str | None = None) -> dict[str, Any]:
        denied = require(role, "get")
        if denied:
            return denied
        org = organization_id
        await self.ensure_hydrated(org)  # type: ignore[attr-defined]
        item = next((a for a in self._bag(org).get("ai_analyses", []) if str(a.get("id")) == str(analysis_id)), None)  # type: ignore[attr-defined]
        if not item:
            return {"ok": False, "error": "not_found", "message_ru": "Анализ не найден"}
        return {"ok": True, "item": item}

    async def archive_ai_analysis(
        self, organization_id: str, analysis_id: str, role: str | None = None, reason: str | None = None
    ) -> dict[str, Any]:
        denied = require(role, "delete")
        if denied:
            # lawyers may archive their analyses with edit
            denied2 = require(role, "edit")
            if denied2:
                return denied2
        org = organization_id
        await self.ensure_hydrated(org)  # type: ignore[attr-defined]
        from datetime import datetime, timezone

        patch = {
            "archived_at": datetime.now(timezone.utc).isoformat(),
            "archived_by": role,
            "archive_reason": reason or "user_archive",
            "status": "archived",
        }
        saved = await self._patch_mem(org, "ai_analysis", analysis_id, patch)  # type: ignore[attr-defined]
        if not saved:
            return {"ok": False, "error": "not_found", "message_ru": "Анализ не найден"}
        await self._activity(  # type: ignore[attr-defined]
            organization_id=org,
            entity_type="ai_analysis",
            entity_id=analysis_id,
            action="ai_analysis_archived",
            summary="AI-анализ архивирован",
            role=role,
        )
        return {"ok": True, "item": saved}

    async def ai_analysis_action(
        self, organization_id: str, analysis_id: str, body: dict[str, Any], role: str | None = None
    ) -> dict[str, Any]:
        """User-confirmed follow-up actions from analysis result — never autonomous."""
        denied = require(role, "ai")
        if denied:
            return denied
        if not body.get("confirm"):
            return {
                "ok": False,
                "error": "confirmation_required",
                "message_ru": "Подтвердите действие (confirm=true). AI не выполняет мутации самостоятельно.",
            }
        action = str(body.get("action") or "").strip()
        forbidden = {"delete", "send", "external_legal", "hard_delete"}
        if action in forbidden:
            return {"ok": False, "error": "forbidden", "message_ru": "AI не может выполнять это действие"}

        org = organization_id
        await self.ensure_hydrated(org)  # type: ignore[attr-defined]
        got = await self.get_ai_analysis(org, analysis_id, role)
        if not got.get("ok"):
            return got
        analysis = got["item"]
        result = analysis.get("result") or {}

        created: dict[str, Any] = {}
        if action == "create_task":
            deadline = body.get("deadline") or {}
            date = deadline.get("date") if isinstance(deadline, dict) else body.get("due_at")
            iso_date = _normalize_date_to_iso(str(date) if date else None)
            title = str(body.get("title") or f"Срок из AI: {date or 'без даты'}").strip()
            task_res = await self.create_task(  # type: ignore[attr-defined]
                org,
                {
                    "title": title,
                    "case_id": body.get("case_id") or analysis.get("case_id"),
                    "client_id": body.get("client_id") or analysis.get("client_id"),
                    "due_at": body.get("due_at")
                    or (f"{iso_date}T12:00:00+00:00" if iso_date else None),
                    "kind": "deadline",
                    "status": "new",
                    "description": body.get("description") or "Создано из AI-анализа",
                    "payload": {"from_analysis_id": analysis_id},
                },
                role,
            )
            if not task_res.get("ok"):
                return task_res
            created["task"] = task_res["item"]
            analysis.setdefault("created_tasks", []).append(task_res["item"]["id"])
            audit_action = "ai_created_task"
        elif action == "create_calendar":
            date = body.get("date") or (body.get("deadline") or {}).get("date")
            title = str(body.get("title") or f"Срок AI: {date or 'событие'}").strip()
            iso_date = _normalize_date_to_iso(str(date) if date else None)
            starts = body.get("starts_at") or (f"{iso_date}T10:00:00+00:00" if iso_date else None)
            if not starts:
                return {"ok": False, "error": "validation", "message_ru": "Укажите starts_at или date"}
            cal_res = await self.create_calendar_event(  # type: ignore[attr-defined]
                org,
                {
                    "title": title,
                    "starts_at": starts,
                    "ends_at": body.get("ends_at"),
                    "case_id": body.get("case_id") or analysis.get("case_id"),
                    "client_id": body.get("client_id") or analysis.get("client_id"),
                    "event_type": body.get("event_type") or "deadline",
                    "description": body.get("description") or "Создано из AI-анализа",
                    "source_kind": "ai_analysis",
                    "source_id": analysis_id,
                    "payload": {"from_analysis_id": analysis_id},
                },
                role,
            )
            if not cal_res.get("ok"):
                return cal_res
            created["event"] = cal_res["item"]
            analysis.setdefault("created_events", []).append(cal_res["item"]["id"])
            audit_action = "ai_created_calendar_event"
        elif action == "attach_case":
            case_id = str(body.get("case_id") or analysis.get("case_id") or "").strip()
            if not case_id:
                return {"ok": False, "error": "validation", "message_ru": "Укажите case_id"}
            patch = {"case_id": case_id, "client_id": body.get("client_id") or analysis.get("client_id")}
            saved = await self._patch_mem(org, "ai_analysis", analysis_id, patch)  # type: ignore[attr-defined]
            created["analysis"] = saved
            audit_action = "ai_analysis_attached_case"
            analysis = saved or analysis
        elif action == "create_draft":
            kind = str(body.get("draft_kind") or "custom")
            draft_body = aiw.build_draft_body(
                kind=kind,
                prompt=str(body.get("prompt") or analysis.get("question") or ""),
                context_text=str((result.get("summary") or "")),
                client_name=None,
                case_title=None,
            )
            doc_res = await self.create_document(  # type: ignore[attr-defined]
                org,
                {
                    "title": body.get("title") or f"AI Draft: {kind}",
                    "doc_type": kind,
                    "status": "ai_draft",
                    "case_id": body.get("case_id") or analysis.get("case_id"),
                    "client_id": body.get("client_id") or analysis.get("client_id"),
                    "content": draft_body,
                    "payload": {
                        "ai_draft": True,
                        "doc_status": "ai_draft",
                        "from_analysis_id": analysis_id,
                        "content": draft_body,
                    },
                },
                role,
            )
            if not doc_res.get("ok"):
                return doc_res
            created["document"] = doc_res["item"]
            analysis.setdefault("created_documents", []).append(doc_res["item"]["id"])
            audit_action = "ai_created_document_draft"
        elif action == "handoff_lawyer":
            created["handoff"] = {
                "mode": body.get("mode") or "consult",
                "analysis_id": analysis_id,
                "case_id": analysis.get("case_id"),
                "client_id": analysis.get("client_id"),
                "question": analysis.get("question"),
            }
            audit_action = "ai_handoff_to_lawyer"
        elif action == "save":
            audit_action = "ai_analysis_saved"
            created["analysis"] = analysis
        else:
            return {"ok": False, "error": "validation", "message_ru": f"Неизвестное действие: {action}"}

        # persist link lists on analysis
        await self._patch_mem(  # type: ignore[attr-defined]
            org,
            "ai_analysis",
            analysis_id,
            {
                "created_tasks": analysis.get("created_tasks") or [],
                "created_events": analysis.get("created_events") or [],
                "created_documents": analysis.get("created_documents") or [],
                "case_id": analysis.get("case_id"),
                "client_id": analysis.get("client_id"),
            },
        )
        await self._activity(  # type: ignore[attr-defined]
            organization_id=org,
            entity_type="ai_analysis",
            entity_id=analysis_id,
            action=audit_action,
            summary=f"AI follow-up: {action}",
            role=role,
            payload={"action": action, "created": {k: (v.get("id") if isinstance(v, dict) else v) for k, v in created.items()}},
        )
        return {"ok": True, "action": action, "created": created, "analysis_id": analysis_id}

    async def ai_lawyer_run(self, organization_id: str, body: dict[str, Any], role: str | None = None) -> dict[str, Any]:
        denied = require(role, "ai")
        if denied:
            return denied
        org = organization_id
        await self.ensure_hydrated(org)  # type: ignore[attr-defined]
        mode = str(body.get("mode") or "consult").strip()
        if mode not in {m["id"] for m in aiw.LAWYER_MODES}:
            mode = "consult"
        prompt = str(body.get("prompt") or body.get("question") or body.get("text") or "").strip()
        if not prompt:
            return {"ok": False, "error": "validation", "message_ru": "Укажите: Что необходимо сделать?"}

        exclude = body.get("exclude_sources") if isinstance(body.get("exclude_sources"), list) else []
        pack = self.build_context_pack(
            org,
            client_id=body.get("client_id"),
            case_id=body.get("case_id"),
            document_ids=body.get("document_ids") if isinstance(body.get("document_ids"), list) else None,
            contract_id=body.get("contract_id"),
            hearing_id=body.get("hearing_id"),
            change_id=body.get("change_id"),
            exclude=[str(x) for x in exclude],
            role=role,
        )
        if not pack.get("ok"):
            return pack

        # optional attachment text
        resolved = self._resolve_target_text(org, body)
        context_text = (pack.get("context_text") or "") + ("\n" + resolved["context_text"] if resolved["context_text"] else "")

        llm = await aiw.maybe_llm_complete(f"AI Lawyer mode={mode} prompt={prompt}\n{context_text[:3000]}")
        provider_meta = {
            "provider": llm.get("provider") or "legal_ops_deterministic",
            "model": llm.get("model") or "rules-v1",
            "mocked": True,
        }

        # Lawyer 3.6: explicit classification of what the answer is based on.
        # Never fabricate laws / court decisions / registry data — missing info is a DATA GAP.
        ados_facts = [s["label"] for s in pack["sources"]]
        user_provided: list[str] = [f"Запрос пользователя: {prompt[:200]}"]
        if resolved.get("context_text"):
            user_provided.append("Приложенный пользователем файл/текст")
        data_gaps: list[str] = []
        if not any(s["kind"] == "case" for s in pack["sources"]):
            data_gaps.append("Дело не привязано к запросу — факты дела недоступны.")
        if not any(s["kind"] == "document" for s in pack["sources"]):
            data_gaps.append("Документы не приложены — содержание документов не анализировалось.")
        data_gaps.append(
            "Внешние проверенные источники (суды, реестры, законодательство) не подключены — эти сведения не проверялись и не приводятся."
        )
        source_classification = {
            "ados_facts": ados_facts,
            "ados_facts_label_ru": "Факты из данных ADOS",
            "user_provided": user_provided,
            "user_provided_label_ru": "Данные, предоставленные пользователем",
            "external_verified": [],
            "external_verified_label_ru": "Внешние проверенные данные",
            "external_note_ru": "Внешние проверенные источники не подключены.",
            "data_gaps": data_gaps,
            "data_gaps_label_ru": "Недостающая информация (DATA GAP)",
        }

        draft_doc = None
        reply_sections: dict[str, Any] = {
            "mode": mode,
            "answer": f"Режим «{next((m['label_ru'] for m in aiw.LAWYER_MODES if m['id']==mode), mode)}»: ответ подготовлен по внутреннему контексту.",
            "disclaimer": "AI Draft / рабочий ответ. Не является финальной юридической консультацией.",
            "sources_panel": {
                "internal_documents": [s for s in pack["sources"] if s["kind"] in {"document", "contract"}],
                "case_data": [s for s in pack["sources"] if s["kind"] in {"case", "client", "task", "hearing", "monitor_change"}],
                "external_legal": [],
                "note_ru": "Использованы только внутренние данные Legal Ops. Внешние госреестры не подключены.",
            },
            "source_classification": source_classification,
            "inspector": pack.get("inspector"),
        }
        if llm.get("ok") and llm.get("text"):
            reply_sections["answer"] = str(llm["text"])[:2000]

        if mode == "draft_document" or any(k in prompt.lower() for k in ("претенз", "договор", "заявлен", "иск", "расписк", "доверен")):
            kind = str(body.get("draft_kind") or "claim")
            if "договор" in prompt.lower() and "доп" not in prompt.lower():
                kind = "contract"
            elif "претенз" in prompt.lower() and "ответ" in prompt.lower():
                kind = "claim_response"
            elif "претенз" in prompt.lower():
                kind = "claim"
            elif "иск" in prompt.lower():
                kind = "lawsuit_draft"
            client_name = None
            case_title = None
            if body.get("client_id"):
                cl = next((c for c in self._bag(org)["clients"] if str(c.get("id")) == str(body.get("client_id"))), None)  # type: ignore[attr-defined]
                client_name = cl.get("name") if cl else None
            if body.get("case_id"):
                cs = next((c for c in self._bag(org)["cases"] if str(c.get("id")) == str(body.get("case_id"))), None)  # type: ignore[attr-defined]
                case_title = cs.get("title") if cs else None
            draft_text = aiw.build_draft_body(
                kind=kind,
                prompt=prompt,
                context_text=context_text,
                client_name=client_name,
                case_title=case_title,
            )
            doc_res = await self.create_document(  # type: ignore[attr-defined]
                org,
                {
                    "title": body.get("title") or f"AI Draft — {kind}",
                    "doc_type": kind,
                    "status": "ai_draft",
                    "case_id": body.get("case_id"),
                    "client_id": body.get("client_id"),
                    "content": draft_text,
                    "payload": {
                        "ai_draft": True,
                        "doc_status": "ai_draft",
                        "content": draft_text,
                        "editable": True,
                    },
                },
                role,
            )
            if doc_res.get("ok"):
                draft_doc = doc_res["item"]
                reply_sections["draft"] = {
                    "document_id": draft_doc["id"],
                    "status": "ai_draft",
                    "status_label": aiw.DOC_STATUSES["ai_draft"],
                    "content": draft_text,
                    "kind": kind,
                }

        structured = None
        if mode in {"review_document", "compare", "research", "position", "case_plan", "consult"}:
            structured = aiw.build_structured_analysis(
                action="summarize" if mode == "consult" else ("compare" if mode == "compare" else "action_plan"),
                question=prompt,
                context_text=context_text,
                target_type="case" if body.get("case_id") else "client",
                target_id=str(body.get("case_id") or body.get("client_id") or ""),
                provider_meta=provider_meta,
            )
            reply_sections["structured"] = structured

        item = {
            "id": str(uuid.uuid4()),
            "organization_id": org,
            "tenant_id": org,
            "workspace_kind": "lawyer",
            "action": None,
            "mode": mode,
            "target_type": "case" if body.get("case_id") else "client",
            "target_id": str(body.get("case_id") or body.get("client_id") or ""),
            "client_id": body.get("client_id"),
            "case_id": body.get("case_id"),
            "question": prompt,
            "result": reply_sections,
            "sources": pack.get("sources"),
            "context_snapshot": {"inspector": pack.get("inspector"), "excluded": exclude},
            "provider_meta": provider_meta,
            "created_tasks": [],
            "created_events": [],
            "created_documents": [draft_doc["id"]] if draft_doc else [],
            "actor_role": role,
            "actor_id": body.get("actor_id") or role,
            "status": "active",
            "payload": {"workspace": "ai_lawyer"},
        }
        saved = await self._persist("ai_analysis", item)  # type: ignore[attr-defined]
        if not saved.get("created_at"):
            from datetime import datetime, timezone

            saved["created_at"] = datetime.now(timezone.utc).isoformat()
        self._bag(org).setdefault("ai_analyses", []).insert(0, saved)  # type: ignore[attr-defined]

        await self._activity(  # type: ignore[attr-defined]
            organization_id=org,
            entity_type="ai_lawyer",
            entity_id=saved["id"],
            action="ai_lawyer_run",
            summary=f"AI-юрист: режим {mode}",
            role=role,
            payload={"analysis_id": saved["id"], "mode": mode, "draft_id": draft_doc["id"] if draft_doc else None},
        )
        return {
            "ok": True,
            "item": saved,
            "reply": reply_sections,
            "draft": reply_sections.get("draft"),
            "context": {"inspector": pack.get("inspector"), "sources": pack.get("sources")},
        }

    async def update_ai_draft(
        self, organization_id: str, document_id: str, body: dict[str, Any], role: str | None = None
    ) -> dict[str, Any]:
        denied = require(role, "edit")
        if denied:
            return denied
        org = organization_id
        await self.ensure_hydrated(org)  # type: ignore[attr-defined]
        doc = next((d for d in self._bag(org)["documents"] if str(d.get("id")) == str(document_id)), None)  # type: ignore[attr-defined]
        if not doc:
            return {"ok": False, "error": "not_found", "message_ru": "Документ не найден"}
        if body.get("overwrite") is not True and body.get("save_as_new"):
            content = str(body.get("content") or "")
            return await self.create_document(  # type: ignore[attr-defined]
                org,
                {
                    "title": body.get("title") or f"{doc.get('title')} (копия)",
                    "doc_type": doc.get("doc_type"),
                    "status": body.get("status") or "ai_draft",
                    "case_id": body.get("case_id") or doc.get("case_id"),
                    "client_id": body.get("client_id") or doc.get("client_id"),
                    "content": content,
                    "payload": {
                        **(doc.get("payload") or {}),
                        "content": content,
                        "ai_draft": True,
                        "doc_status": body.get("status") or "ai_draft",
                        "copied_from": document_id,
                    },
                },
                role,
            )
        if body.get("overwrite") is not True and body.get("content") is not None and not body.get("confirm_overwrite"):
            return {
                "ok": False,
                "error": "confirmation_required",
                "message_ru": "Для перезаписи оригинала укажите confirm_overwrite=true или save_as_new=true",
            }
        payload = dict(doc.get("payload") or {})
        if body.get("content") is not None:
            payload["content"] = str(body.get("content"))
            payload["content_preview"] = str(body.get("content"))[:500]
        if body.get("status"):
            payload["doc_status"] = body.get("status")
        patch: dict[str, Any] = {"payload": payload}
        if body.get("status"):
            patch["status"] = body.get("status")
        if body.get("case_id"):
            patch["case_id"] = body.get("case_id")
        if body.get("client_id"):
            patch["client_id"] = body.get("client_id")
        if body.get("title"):
            patch["title"] = body.get("title")
        saved = await self._patch_mem(org, "document", document_id, patch)  # type: ignore[attr-defined]
        await self._activity(  # type: ignore[attr-defined]
            organization_id=org,
            entity_type="document",
            entity_id=document_id,
            action="ai_draft_updated",
            summary="AI-черновик обновлён",
            role=role,
            payload={"document_id": document_id, "status": patch.get("status")},
        )
        return {"ok": True, "item": saved}

    async def regenerate_draft_fragment(
        self, organization_id: str, document_id: str, body: dict[str, Any], role: str | None = None
    ) -> dict[str, Any]:
        denied = require(role, "ai")
        if denied:
            return denied
        org = organization_id
        await self.ensure_hydrated(org)  # type: ignore[attr-defined]
        doc = next((d for d in self._bag(org)["documents"] if str(d.get("id")) == str(document_id)), None)  # type: ignore[attr-defined]
        if not doc:
            return {"ok": False, "error": "not_found"}
        content = str((doc.get("payload") or {}).get("content") or "")
        fragment = str(body.get("fragment") or body.get("selected") or "")
        instruction = str(body.get("instruction") or "Переформулируй выбранный фрагмент яснее")
        llm = await aiw.maybe_llm_complete(f"{instruction}\nFRAGMENT:\n{fragment or content[:400]}")
        replacement = str(llm.get("text") or f"[перегенерация] {fragment or '…'}")[:2000]
        if fragment and fragment in content:
            new_content = content.replace(fragment, replacement, 1)
        else:
            new_content = content + "\n\n## Перегенерация\n" + replacement
        return {
            "ok": True,
            "preview_content": new_content,
            "replacement": replacement,
            "message_ru": "Черновик не сохранён автоматически — подтвердите сохранение в редакторе.",
        }

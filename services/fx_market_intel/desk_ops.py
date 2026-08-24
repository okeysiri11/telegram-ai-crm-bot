"""Desk operations: paper account, journal, signals, notifications, calendar."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from services.fx_market_intel.calendar_events import filter_events, make_event
from services.fx_market_intel.journal import journal_from_closed_position, journal_position_opened
from services.fx_market_intel.notifications import create_notification, transition
from services.fx_market_intel.paper_trading import (
    account_snapshot,
    assert_paper_only,
    cancel_pending,
    check_sl_tp,
    close_position,
    create_paper_order,
    mark_position,
    new_account,
    risk_preview,
    try_fill_limit,
    validate_risk_agent,
    validate_sl_tp_vs_side,
    INITIAL_BALANCE_USD,
)
from services.fx_market_intel.signals import assert_no_trade_execution, create_signal, evaluate_price_trigger
from services.fx_market_intel.symbols import normalize_symbol

logger = logging.getLogger(__name__)


class FxDeskOps:
    def __init__(self) -> None:
        self._orders: dict[str, list[dict[str, Any]]] = {}
        self._positions: dict[str, list[dict[str, Any]]] = {}
        self._journal: dict[str, list[dict[str, Any]]] = {}
        self._manual_signals: dict[str, list[dict[str, Any]]] = {}
        self._accounts: dict[str, dict[str, Any]] = {}
        self._notifications: dict[str, list[dict[str, Any]]] = {}
        self._manual_events: dict[str, list[dict[str, Any]]] = {}
        self._idempotency: dict[str, dict[str, Any]] = {}
        self._hydrated: set[str] = set()
        # Sprint 50.6: SL/TP auto-close runs on GET/refresh mark poll only — no aggressive background worker.
        self.sl_tp_auto_trigger_mode = "on_refresh"
        self.sl_tp_background_deferred = True

    def _t(self, tenant_id: str) -> str:
        return tenant_id or "default"

    async def ensure_hydrated(self, tenant_id: str) -> None:
        """Load durable paper state from Postgres into process memory (once per tenant)."""
        key = self._t(tenant_id)
        if key in self._hydrated:
            return
        try:
            from database.session import get_session
            from repositories.fx_market_intel_repository import FxMarketIntelRepository

            async with get_session() as session:
                repo = FxMarketIntelRepository(session)
                orders = await repo.list_paper_orders(key)
                positions = await repo.list_paper_positions(key)
                journal = await repo.list_journal_entries(key)

            def _payload(row: Any) -> dict[str, Any]:
                raw = getattr(row, "payload", None)
                if isinstance(raw, dict) and raw:
                    out = dict(raw)
                else:
                    out = {}
                # Ensure keys exist even if payload thin
                if hasattr(row, "order_key"):
                    out.setdefault("order_id", row.order_key)
                    out.setdefault("status", getattr(row, "status", None))
                    out.setdefault("instrument", getattr(row, "instrument", None))
                    out.setdefault("side", getattr(row, "side", None))
                    out.setdefault("fill_price", getattr(row, "fill_price", None))
                if hasattr(row, "position_key"):
                    out.setdefault("position_id", row.position_key)
                    out.setdefault("order_id", getattr(row, "order_key", None))
                    out.setdefault("status", getattr(row, "status", None))
                    out.setdefault("instrument", getattr(row, "instrument", None))
                    out.setdefault("side", getattr(row, "side", None))
                    out.setdefault("entry_price", getattr(row, "entry_price", None))
                    out.setdefault("exit_price", getattr(row, "exit_price", None))
                    out.setdefault("pnl", getattr(row, "pnl", None))
                    out.setdefault("stop_loss", getattr(row, "stop_loss", None))
                    out.setdefault("take_profit", getattr(row, "take_profit", None))
                if hasattr(row, "journal_key"):
                    out.setdefault("journal_id", row.journal_key)
                    out.setdefault("instrument", getattr(row, "instrument", None))
                    out.setdefault("entry", getattr(row, "entry_price", None))
                    out.setdefault("exit", getattr(row, "exit_price", None))
                    out.setdefault("pnl", getattr(row, "pnl", None))
                out.setdefault("tenant_id", key)
                out.setdefault("paper", True)
                out.setdefault("trade_execution", False)
                return out

            # Merge DB under memory (memory wins for same id — allows in-process updates)
            db_orders = [_payload(r) for r in orders]
            db_pos = [_payload(r) for r in positions]
            db_jn = [_payload(r) for r in journal]

            mem_o = {o.get("order_id"): o for o in self._orders.get(key, []) if o.get("order_id")}
            for o in db_orders:
                oid = o.get("order_id")
                if oid and oid not in mem_o:
                    mem_o[oid] = o
            self._orders[key] = sorted(mem_o.values(), key=lambda x: str(x.get("created_at") or ""), reverse=True)

            mem_p = {p.get("position_id"): p for p in self._positions.get(key, []) if p.get("position_id")}
            for p in db_pos:
                pid = p.get("position_id")
                if pid and pid not in mem_p:
                    mem_p[pid] = p
            self._positions[key] = sorted(mem_p.values(), key=lambda x: str(x.get("opened_at") or x.get("created_at") or ""), reverse=True)

            mem_j = {j.get("journal_id"): j for j in self._journal.get(key, []) if j.get("journal_id")}
            for j in db_jn:
                jid = j.get("journal_id")
                if jid and jid not in mem_j:
                    mem_j[jid] = j
            self._journal[key] = sorted(mem_j.values(), key=lambda x: str(x.get("created_at") or ""), reverse=True)

            # Reconstruct account aggregates from journal closes
            if key not in self._accounts:
                self._accounts[key] = new_account(key)
            acc = self._accounts[key]
            closed = [j for j in self._journal[key] if str(j.get("event") or j.get("kind") or "") == "PAPER_POSITION_CLOSED" or j.get("exit") is not None]
            if closed and not acc.get("realized_pnl"):
                rpnl = sum(float(j.get("pnl") or 0) for j in closed)
                wins = sum(1 for j in closed if float(j.get("pnl") or 0) > 0)
                acc["realized_pnl"] = round(rpnl, 6)
                acc["trades_count"] = len(closed)
                acc["wins"] = wins
                acc["win_rate"] = round(100.0 * wins / len(closed), 2) if closed else 0.0

            # Restore idempotency keys from order payloads
            bag = self._idempotency.setdefault(key, {})
            for o in self._orders[key]:
                idem = o.get("idempotency_key")
                if idem and idem not in bag:
                    bag[idem] = {
                        "ok": True,
                        "order": o,
                        "position": next((p for p in self._positions[key] if p.get("order_id") == o.get("order_id")), None),
                        "paper": True,
                        "trade_execution": False,
                        "idempotent_replay": True,
                    }
        except Exception as exc:
            logger.warning("paper hydrate skipped: %s", exc)
        self._hydrated.add(key)

    def get_account(self, tenant_id: str) -> dict[str, Any]:
        key = self._t(tenant_id)
        if key not in self._accounts:
            self._accounts[key] = new_account(key)
        return account_snapshot(
            self._accounts[key],
            self._positions.get(key, []),
            self._journal.get(key, []),
        )

    async def get_account_async(self, tenant_id: str) -> dict[str, Any]:
        await self.ensure_hydrated(tenant_id)
        return self.get_account(tenant_id)

    async def _mark(self, instrument: str) -> float | None:
        from services.fx_market_intel import get_fx_market_intel

        q = await get_fx_market_intel().quote(instrument)
        if q.get("status") != "connected" or q.get("mid") is None:
            return None
        try:
            return float(q["mid"])
        except Exception:
            return None

    async def create_manual_signal(
        self,
        *,
        tenant_id: str,
        instrument: str,
        signal: str,
        timeframe: str = "1H",
        confidence: float = 0.5,
        reasons: list[str] | None = None,
        analysis_run_id: str | None = None,
        price_trigger: dict[str, Any] | None = None,
        source: str = "chart",
    ) -> dict[str, Any]:
        mark = await self._mark(instrument)
        sig = create_signal(
            instrument=normalize_symbol(instrument),
            timeframe=timeframe,
            signal=signal,
            confidence=confidence,
            reasons=reasons or ["Создан оператором"],
            tenant_id=self._t(tenant_id),
            analysis_run_id=analysis_run_id,
            price_at_signal=mark,
            price_trigger=price_trigger,
            source=source,
        )
        sig["lifecycle"] = "ACTIVE"
        assert_no_trade_execution(sig)
        key = self._t(tenant_id)
        self._manual_signals.setdefault(key, []).insert(0, sig)
        self._manual_signals[key] = self._manual_signals[key][:100]
        try:
            from services.fx_market_intel import get_fx_market_intel

            svc = get_fx_market_intel()
            svc._signals.insert(0, sig)
            svc._signals = svc._signals[:100]
        except Exception:
            pass
        notif = create_notification(
            tenant_id=key,
            signal_id=sig["signal_id"],
            title=f"Сигнал {sig['instrument']}: {sig.get('status_ru') or sig['signal']}",
            body="; ".join(sig.get("reasons") or [])[:200],
            instrument=sig["instrument"],
            status="ACTIVE",
        )
        self._notifications.setdefault(key, []).insert(0, notif)
        await self._persist_signal(sig)
        return sig

    async def place_paper_order(self, *, tenant_id: str, body: dict[str, Any]) -> dict[str, Any]:
        key = self._t(tenant_id)
        await self.ensure_hydrated(key)
        idem = str(body.get("idempotency_key") or body.get("client_request_id") or "").strip()
        if idem:
            bag = self._idempotency.setdefault(key, {})
            if idem in bag:
                return {**bag[idem], "idempotent_replay": True}
        instrument = normalize_symbol(str(body.get("instrument") or "EUR/USD"))
        mark = await self._mark(instrument)
        if mark is None and str(body.get("order_type") or "MARKET").upper() == "MARKET":
            return {
                "ok": False,
                "error": "quote_unavailable",
                "message_ru": f"Не удалось получить котировку {instrument}",
                "paper": True,
                "trade_execution": False,
            }
        # Risk preview + Risk Agent soft check
        entry = float(body["entry_price"]) if body.get("entry_price") is not None else (float(mark) if mark is not None else 0.0)
        if body.get("limit_price") is not None and str(body.get("order_type") or "").upper() == "LIMIT":
            entry = float(body["limit_price"])
        sl_v = float(body["stop_loss"]) if body.get("stop_loss") is not None else None
        tp_v = float(body["take_profit"]) if body.get("take_profit") is not None else None
        side_v = str(body.get("side") or "BUY")
        levels = validate_sl_tp_vs_side(side=side_v, entry=entry or 0.0, stop_loss=sl_v, take_profit=tp_v)
        if not levels.get("ok"):
            return {
                "ok": False,
                "error": levels.get("error"),
                "message_ru": levels.get("message_ru"),
                "paper": True,
                "trade_execution": False,
            }
        qty = float(body.get("quantity") or body.get("position_size") or 1)
        preview = risk_preview(
            entry=entry or 0.0,
            stop_loss=sl_v,
            take_profit=tp_v,
            quantity=qty,
            side=side_v,
            balance=float(self.get_account(key).get("balance") or INITIAL_BALANCE_USD),
        )
        risk_settings = body.get("risk_settings") if isinstance(body.get("risk_settings"), dict) else {}
        open_n = len([p for p in self._positions.get(key, []) if str(p.get("status", "")).upper() == "OPEN"])
        risk_check = validate_risk_agent(risk_settings=risk_settings, preview=preview, open_positions=open_n)
        if not risk_check.get("ok"):
            return {
                "ok": False,
                "error": "risk_agent_blocked",
                "message_ru": (risk_check.get("warnings") or ["Risk Agent: сделка отклонена"])[0],
                "risk_warnings": risk_check.get("warnings"),
                "risk": preview,
                "paper": True,
                "trade_execution": False,
            }
        result = create_paper_order(
            tenant_id=self._t(tenant_id),
            instrument=instrument,
            side=str(body.get("side") or "BUY"),
            order_type=str(body.get("order_type") or "MARKET"),
            quantity=float(body.get("quantity") or body.get("position_size") or 1),
            limit_price=float(body["limit_price"]) if body.get("limit_price") is not None else None,
            entry_price=float(body["entry_price"]) if body.get("entry_price") is not None else None,
            stop_loss=float(body["stop_loss"]) if body.get("stop_loss") is not None else None,
            take_profit=float(body["take_profit"]) if body.get("take_profit") is not None else None,
            signal_id=body.get("signal_id"),
            analysis_run_id=body.get("analysis_run_id"),
            agent_result_id=body.get("agent_result_id"),
            mark_price=mark,
            notes=str(body.get("notes") or ""),
            draft=bool(body.get("draft")),
        )
        order = result["order"]
        order["risk"] = preview
        order["risk_warnings"] = risk_check.get("warnings") or []
        if idem:
            order["idempotency_key"] = idem
        self.get_account(key)
        self._orders.setdefault(key, []).insert(0, order)
        if result.get("position"):
            self._positions.setdefault(key, []).insert(0, result["position"])
            self._manual_events.setdefault(key, []).append(
                make_event(
                    category="PAPER_TRADE",
                    title=f"Открыта бумажная {order['side']} {instrument}",
                    scheduled_at=order.get("filled_at") or order["created_at"],
                    instrument=instrument,
                    source="paper",
                    status="open",
                    links={
                        "paper": f"?view=paper&order_id={order['order_id']}",
                        "signal": f"?view=signals&signal_id={order.get('signal_id')}" if order.get("signal_id") else None,
                        "analysis": f"?view=intel_history&run_id={order.get('analysis_run_id')}" if order.get("analysis_run_id") else None,
                    },
                    tenant_id=key,
                )
            )
        journal_open = None
        if result.get("position"):
            journal_open = journal_position_opened(result["position"], order)
            self._journal.setdefault(key, []).insert(0, journal_open)
        persist_ok = await self._persist_order(order, result.get("position"), journal_open)
        if not persist_ok:
            # Still keep in-memory for this process, but surface durable write failure
            return {
                "ok": False,
                "error": "persist_failed",
                "message_ru": "Сервер не сохранил сделку",
                "order": order,
                "position": result.get("position"),
                "paper": True,
                "trade_execution": False,
            }
        out = {
            **result,
            "ok": True,
            "order_id": order.get("order_id"),
            "position_id": (result.get("position") or {}).get("position_id"),
            "journal": journal_open,
            "journal_id": (journal_open or {}).get("journal_id"),
            "account": self.get_account(key),
            "risk": preview,
            "risk_warnings": risk_check.get("warnings") or [],
            "message_ru": f"Бумажная сделка {instrument} открыта",
            "sl_tp_auto_trigger": {
                "mode": self.sl_tp_auto_trigger_mode,
                "background_deferred": self.sl_tp_background_deferred,
                "note_ru": "Авто SL/TP срабатывает при обновлении бумажного стола (без агрессивного polling).",
            },
        }
        if idem:
            self._idempotency.setdefault(key, {})[idem] = out
        # notification: position opened
        if result.get("position"):
            notif = create_notification(
                tenant_id=key,
                signal_id=str(order.get("signal_id") or order["order_id"]),
                title=f"Бумажная сделка {instrument} открыта",
                body=f"{order['side']} · вход {result['position'].get('entry_price')} · SL {order.get('stop_loss')} · TP {order.get('take_profit')}",
                instrument=instrument,
                status="ACTIVE",
            )
            notif["kind"] = "paper_opened"
            notif["links"] = {
                "paper": f"?view=paper&order_id={order['order_id']}",
                "journal": f"?view=journal&journal_id={(journal_open or {}).get('journal_id')}",
            }
            self._notifications.setdefault(key, []).insert(0, notif)
        return out

    async def cancel_paper_order(self, *, tenant_id: str, order_id: str) -> dict[str, Any]:
        key = self._t(tenant_id)
        await self.ensure_hydrated(key)
        orders = self._orders.get(key, [])
        order = next((o for o in orders if o.get("order_id") == order_id), None)
        if not order:
            return {"ok": False, "error": "order_not_found"}
        try:
            cancelled = cancel_pending(order)
        except Exception as exc:
            return {"ok": False, "error": str(exc)}
        self._orders[key] = [cancelled if o.get("order_id") == order_id else o for o in orders]
        return {"ok": True, "order": cancelled}

    async def refresh_paper(self, tenant_id: str) -> dict[str, Any]:
        key = self._t(tenant_id)
        await self.ensure_hydrated(key)
        filled = 0
        closed = 0
        new_orders = []
        for order in list(self._orders.get(key, [])):
            st = str(order.get("status", "")).upper()
            ot = str(order.get("order_type", "")).upper()
            if st == "PENDING" and ot == "LIMIT":
                mark = await self._mark(order["instrument"])
                if mark is None:
                    new_orders.append(order)
                    continue
                # normalize for try_fill_limit
                norm = {**order, "status": "PENDING", "order_type": "LIMIT"}
                hit = try_fill_limit(norm, mark)
                if hit:
                    new_orders.append(hit["order"])
                    self._positions.setdefault(key, []).insert(0, hit["position"])
                    filled += 1
                    j_open = journal_position_opened(hit["position"], hit["order"])
                    self._journal.setdefault(key, []).insert(0, j_open)
                    inst = str(hit["order"].get("instrument") or "EUR/USD")
                    notif = create_notification(
                        tenant_id=key,
                        signal_id=str(hit["order"].get("signal_id") or hit["order"]["order_id"]),
                        title=f"Бумажная сделка {inst} открыта",
                        body=f"LIMIT fill · {hit['order'].get('side')}",
                        instrument=inst,
                        status="ACTIVE",
                    )
                    notif["kind"] = "paper_opened"
                    notif["links"] = {"paper": "?view=paper", "journal": f"?view=journal&journal_id={j_open.get('journal_id')}"}
                    self._notifications.setdefault(key, []).insert(0, notif)
                    await self._persist_order(hit["order"], hit["position"], j_open)
                else:
                    new_orders.append(order)
            else:
                new_orders.append(order)
        self._orders[key] = new_orders

        new_pos = []
        for pos in list(self._positions.get(key, [])):
            if str(pos.get("status", "")).upper() != "OPEN":
                new_pos.append(pos)
                continue
            mark = await self._mark(pos["instrument"])
            if mark is None:
                new_pos.append(pos)
                continue
            marked = mark_position(pos, mark)
            closed_pos = check_sl_tp(marked, mark)
            if closed_pos:
                new_pos.append(closed_pos)
                closed += 1
                j = journal_from_closed_position(
                    closed_pos,
                    market_context={"mark": mark, "source": "paper_sl_tp"},
                    consensus=None,
                    notes=str(closed_pos.get("notes") or ""),
                )
                self._journal.setdefault(key, []).insert(0, j)
                acc = self._accounts.setdefault(key, new_account(key))
                acc["realized_pnl"] = float(acc.get("realized_pnl") or 0) + float(closed_pos.get("pnl") or 0)
                acc["trades_count"] = int(acc.get("trades_count") or 0) + 1
                if float(closed_pos.get("pnl") or 0) > 0:
                    acc["wins"] = int(acc.get("wins") or 0) + 1
                reason = str(closed_pos.get("close_reason") or "")
                inst = str(closed_pos.get("instrument") or "EUR/USD")
                if reason == "stop_loss":
                    title = f"{inst} достиг Stop Loss"
                elif reason == "take_profit":
                    title = f"{inst} достиг Take Profit"
                else:
                    title = f"Бумажная позиция {inst} закрыта. P&L: {closed_pos.get('pnl')}"
                notif = create_notification(
                    tenant_id=key,
                    signal_id=str(closed_pos.get("signal_id") or closed_pos.get("order_id") or closed_pos.get("position_id")),
                    title=title,
                    body=f"P&L: {closed_pos.get('pnl')} · причина: {reason or 'sl_tp'}",
                    instrument=inst,
                    status="TRIGGERED",
                )
                notif["kind"] = reason or "paper_closed"
                notif["links"] = {"paper": "?view=paper", "journal": f"?view=journal&journal_id={j.get('journal_id')}"}
                self._notifications.setdefault(key, []).insert(0, notif)
                close_notif = create_notification(
                    tenant_id=key,
                    signal_id=str(closed_pos.get("position_id")),
                    title=f"Бумажная позиция {inst} закрыта. P&L: {closed_pos.get('pnl')}",
                    body=str(closed_pos.get("close_reason") or "sl_tp"),
                    instrument=inst,
                    status="ACTIVE",
                )
                close_notif["kind"] = "paper_closed"
                close_notif["links"] = {"journal": f"?view=journal&journal_id={j.get('journal_id')}", "paper": "?view=paper"}
                self._notifications.setdefault(key, []).insert(0, close_notif)
                await self._persist_position(closed_pos, j)
            else:
                new_pos.append(marked)
        self._positions[key] = new_pos

        triggered = 0
        try:
            from services.fx_market_intel import get_fx_market_intel

            svc = get_fx_market_intel()
            updated = []
            for sig in await svc.list_signals(key):
                mark = await self._mark(str(sig.get("instrument") or "EUR/USD"))
                if mark is None:
                    updated.append(sig)
                    continue
                ns = evaluate_price_trigger(sig, mark)
                was = bool((sig.get("price_trigger") or {}).get("triggered"))
                now = bool((ns.get("price_trigger") or {}).get("triggered"))
                if now and not was:
                    triggered += 1
                    ns["lifecycle"] = "TRIGGERED"
                    notif = create_notification(
                        tenant_id=key,
                        signal_id=ns["signal_id"],
                        title=f"Сигнал сработал: {ns.get('instrument')}",
                        body="Ценовой триггер",
                        instrument=str(ns.get("instrument") or "EUR/USD"),
                        status="TRIGGERED",
                    )
                    self._notifications.setdefault(key, []).insert(0, notif)
                updated.append(ns)
            svc._signals = [s for s in updated if s.get("tenant_id") in ("", key, "default")][:100]
        except Exception as exc:
            logger.warning("trigger refresh skipped: %s", exc)

        return {
            "filled_limits": filled,
            "closed_sl_tp": closed,
            "triggers_fired": triggered,
            "account": self.get_account(key),
            "orders": self.list_orders(key),
            "positions": self.list_positions(key),
            "journal": self.list_journal(key),
            "paper": True,
            "trade_execution": False,
            "sl_tp_auto_trigger": {
                "mode": self.sl_tp_auto_trigger_mode,
                "background_deferred": self.sl_tp_background_deferred,
            },
        }

    async def close_paper_position(
        self, *, tenant_id: str, position_id: str, notes: str = ""
    ) -> dict[str, Any]:
        key = self._t(tenant_id)
        await self.ensure_hydrated(key)
        pos = next((p for p in self._positions.get(key, []) if p.get("position_id") == position_id), None)
        if not pos:
            return {"ok": False, "error": "position_not_found", "message_ru": "Позиция не найдена"}
        if str(pos.get("status", "")).upper() != "OPEN":
            return {"ok": False, "error": "not_open", "message_ru": "Позиция уже закрыта"}
        mark = await self._mark(pos["instrument"])
        if mark is None:
            return {
                "ok": False,
                "error": "quote_unavailable",
                "message_ru": f"Не удалось получить котировку {pos.get('instrument')}",
            }
        closed = close_position(pos, exit_price=mark, reason="manual")
        self._positions[key] = [closed if p.get("position_id") == position_id else p for p in self._positions[key]]
        j = journal_from_closed_position(
            closed,
            notes=notes,
            market_context={"mark": mark, "closed_manually": True},
        )
        self._journal.setdefault(key, []).insert(0, j)
        acc = self._accounts.setdefault(key, new_account(key))
        acc["realized_pnl"] = float(acc.get("realized_pnl") or 0) + float(closed.get("pnl") or 0)
        acc["trades_count"] = int(acc.get("trades_count") or 0) + 1
        if float(closed.get("pnl") or 0) > 0:
            acc["wins"] = int(acc.get("wins") or 0) + 1
        inst = str(closed.get("instrument") or "EUR/USD")
        notif = create_notification(
            tenant_id=key,
            signal_id=str(closed.get("position_id")),
            title=f"Бумажная позиция {inst} закрыта. P&L: {closed.get('pnl')}",
            body=notes or "Закрыто вручную",
            instrument=inst,
            status="ACTIVE",
        )
        notif["kind"] = "paper_closed"
        notif["links"] = {"journal": f"?view=journal&journal_id={j.get('journal_id')}", "paper": "?view=paper"}
        self._notifications.setdefault(key, []).insert(0, notif)
        persist_ok = await self._persist_position(closed, j)
        if not persist_ok:
            return {
                "ok": False,
                "error": "persist_failed",
                "message_ru": "Сервер не сохранил сделку",
                "position": closed,
                "journal": j,
            }
        return {
            "ok": True,
            "position": closed,
            "journal": j,
            "journal_id": j.get("journal_id"),
            "account": self.get_account(key),
            "message_ru": f"Бумажная позиция {inst} закрыта. P&L: {closed.get('pnl')}",
        }

    def list_orders(self, tenant_id: str) -> list[dict[str, Any]]:
        return list(self._orders.get(self._t(tenant_id), []))

    def list_positions(self, tenant_id: str) -> list[dict[str, Any]]:
        return list(self._positions.get(self._t(tenant_id), []))

    def list_journal(self, tenant_id: str) -> list[dict[str, Any]]:
        return list(self._journal.get(self._t(tenant_id), []))

    def list_notifications(self, tenant_id: str) -> list[dict[str, Any]]:
        return list(self._notifications.get(self._t(tenant_id), []))

    def act_notification(self, tenant_id: str, notification_id: str, action: str) -> dict[str, Any]:
        key = self._t(tenant_id)
        items = self._notifications.get(key, [])
        found = next((n for n in items if n.get("notification_id") == notification_id), None)
        if not found:
            return {"ok": False, "error": "not_found"}
        updated = transition(found, action)
        self._notifications[key] = [updated if n.get("notification_id") == notification_id else n for n in items]
        # mirror signal lifecycle
        if updated["status"] == "ACKNOWLEDGED":
            self._set_signal_lifecycle(key, updated.get("signal_id"), "ACKNOWLEDGED")
        if updated["status"] == "DISABLED":
            self._set_signal_lifecycle(key, updated.get("signal_id"), "DISABLED")
        return {"ok": True, "notification": updated}

    def _set_signal_lifecycle(self, tenant_id: str, signal_id: str | None, lifecycle: str) -> None:
        if not signal_id:
            return
        for bag in (self._manual_signals.get(tenant_id, []),):
            for s in bag:
                if s.get("signal_id") == signal_id:
                    s["lifecycle"] = lifecycle
        try:
            from services.fx_market_intel import get_fx_market_intel

            for s in get_fx_market_intel()._signals:
                if s.get("signal_id") == signal_id:
                    s["lifecycle"] = lifecycle
        except Exception:
            pass

    def add_manual_event(self, tenant_id: str, body: dict[str, Any]) -> dict[str, Any]:
        key = self._t(tenant_id)
        scheduled = str(body.get("scheduled_at") or body.get("date") or "")
        if body.get("time") and "T" not in scheduled:
            scheduled = f"{scheduled}T{body.get('time')}:00"
        ev = make_event(
            category=str(body.get("category") or "MANUAL"),
            title=str(body.get("title") or body.get("name") or "Событие"),
            scheduled_at=scheduled or datetime.now(timezone.utc).isoformat(),
            instrument=str(body.get("instrument") or "EUR/USD"),
            source="manual",
            status="scheduled",
            importance=str(body.get("importance") or "medium"),
            description=str(body.get("description") or ""),
            reminder=bool(body.get("reminder")),
            links=body.get("links") if isinstance(body.get("links"), dict) else {},
            tenant_id=key,
        )
        if body.get("create_signal"):
            ev["links"]["create_signal"] = True
        self._manual_events.setdefault(key, []).append(ev)
        return ev

    async def calendar_bundle(self, tenant_id: str, filters: dict[str, bool] | None = None) -> dict[str, Any]:
        key = self._t(tenant_id)
        events: list[dict[str, Any]] = list(self._manual_events.get(key, []))
        # macro
        try:
            from services.fx_market_intel import get_fx_market_intel

            svc = get_fx_market_intel()
            cal = await svc.macro_calendar()
            for e in cal.get("events") or []:
                events.append(
                    make_event(
                        category="MACRO",
                        title=str(e.get("title") or e.get("event") or "Макро"),
                        scheduled_at=str(e.get("scheduled_at") or ""),
                        instrument=(e.get("affected_instruments") or ["EUR/USD"])[0],
                        source=str((cal.get("provider") or {}).get("label") or "macro"),
                        status=str(e.get("status") or "scheduled"),
                        importance=str(e.get("importance") or "medium"),
                        links={"analysis": "?view=analysis", "signal": "?view=signals", "paper": "?view=paper"},
                        tenant_id="global",
                    )
                )
            feed = await svc.news_feed(["EUR/USD", "DXY"])
            for a in (feed.get("items") or [])[:30]:
                events.append(
                    make_event(
                        category="NEWS",
                        title=str(a.get("title") or "Новость"),
                        scheduled_at=str(a.get("published_at") or a.get("fetched_at") or ""),
                        instrument=(a.get("instruments") or ["EUR/USD"])[0] if a.get("instruments") else "EUR/USD",
                        source=str(a.get("source") or "news"),
                        status="published",
                        importance=str(a.get("importance") or "medium"),
                        links={"url": a.get("url")},
                        tenant_id="global",
                    )
                )
            for sig in await svc.list_signals(key):
                events.append(
                    make_event(
                        category="SIGNAL",
                        title=f"Сигнал {sig.get('instrument')}: {sig.get('status_ru') or sig.get('signal')}",
                        scheduled_at=str(sig.get("timestamp") or ""),
                        instrument=str(sig.get("instrument") or "EUR/USD"),
                        source=str(sig.get("source") or "signal"),
                        status=str(sig.get("lifecycle") or "ACTIVE"),
                        importance="high" if float(sig.get("confidence") or 0) > 0.6 else "medium",
                        links={
                            "signal": f"?view=signals&signal_id={sig.get('signal_id')}",
                            "analysis": f"?view=intel_history&run_id={sig.get('analysis_run_id')}" if sig.get("analysis_run_id") else "?view=analysis",
                            "paper": "?view=paper",
                        },
                        tenant_id=key,
                    )
                )
            hist = await svc.history(key, limit=20)
            for h in hist.get("items") or []:
                events.append(
                    make_event(
                        category="ANALYSIS",
                        title=f"Анализ {h.get('preset_id') or h.get('agent') or ''}",
                        scheduled_at=str(h.get("created_at") or ""),
                        instrument=str(h.get("instrument") or "EUR/USD"),
                        source="analysis",
                        status=str(h.get("direction") or "done"),
                        links={"analysis": f"?view=intel_history&run_id={h.get('analysis_run_id') or h.get('analysis_id')}"},
                        tenant_id=key,
                    )
                )
        except Exception as exc:
            logger.warning("calendar aggregate partial: %s", exc)

        # sessions (static daily markers today UTC)
        today = datetime.now(timezone.utc).date()
        for title, hour, cat in (
            ("Сессия Европы", 7, "SESSION"),
            ("Сессия США", 13, "SESSION"),
        ):
            events.append(
                make_event(
                    category=cat,
                    title=title,
                    scheduled_at=datetime(today.year, today.month, today.day, hour, 0, tzinfo=timezone.utc).isoformat(),
                    instrument="EUR/USD",
                    source="session",
                    status="scheduled",
                    importance="low",
                    tenant_id="global",
                )
            )

        enabled = filters or {
            "macro": True,
            "news": True,
            "analysis": True,
            "agent": True,
            "signal": True,
            "session": True,
            "paper": True,
            "manual": True,
        }
        filtered = filter_events(events, enabled)
        filtered.sort(key=lambda e: str(e.get("scheduled_at") or ""))
        return {"events": filtered, "filters": enabled, "categories": sorted({e.get("category") for e in filtered})}

    def cross_links(self, *, signal_id: str | None = None, analysis_run_id: str | None = None, tenant_id: str = "default") -> dict[str, Any]:
        key = self._t(tenant_id)
        positions = [
            p
            for p in self._positions.get(key, [])
            if (not signal_id or p.get("signal_id") == signal_id)
            and (not analysis_run_id or p.get("analysis_run_id") == analysis_run_id)
        ]
        journal = [
            j
            for j in self._journal.get(key, [])
            if (not signal_id or j.get("signal_id") == signal_id)
            and (not analysis_run_id or j.get("analysis_run_id") == analysis_run_id)
        ]
        return {
            "signal_id": signal_id,
            "analysis_run_id": analysis_run_id,
            "positions": positions,
            "journal": journal,
            "notifications": [n for n in self._notifications.get(key, []) if not signal_id or n.get("signal_id") == signal_id],
            "links": {
                "chart": "?view=charts",
                "analysis": f"?view=intel_history&run_id={analysis_run_id}" if analysis_run_id else "?view=analysis",
                "signals": f"?view=signals&signal_id={signal_id}" if signal_id else "?view=signals",
                "paper": "?view=paper",
                "journal": "?view=journal",
                "calendar": "?view=calendar",
                "notifications": "?view=notifications",
            },
        }

    async def _persist_signal(self, sig: dict[str, Any]) -> None:
        try:
            from database.session import get_session
            from repositories.fx_market_intel_repository import FxMarketIntelRepository

            async with get_session() as session:
                repo = FxMarketIntelRepository(session)
                await repo.save_signal(
                    tenant_id=sig.get("tenant_id") or "default",
                    analysis_run_id=sig.get("analysis_run_id"),
                    signal_key=sig["signal_id"],
                    instrument=sig["instrument"],
                    timeframe=sig.get("timeframe"),
                    signal=sig["signal"],
                    confidence=sig.get("confidence"),
                    price_at_signal=sig.get("price_at_signal"),
                    entry_zone=sig.get("entry_zone"),
                    invalidation=sig.get("invalidation"),
                    reasons=sig.get("reasons"),
                    status=sig.get("status") or sig.get("signal"),
                    expires_at=None,
                    analytics_only=True,
                    trade_execution=False,
                    payload=sig,
                )
        except Exception as exc:
            logger.warning("signal persist skipped: %s", exc)

    @staticmethod
    def _persist_soft_skip(exc: Exception) -> bool:
        msg = str(exc).lower()
        return any(
            token in msg
            for token in (
                "connect",
                "connection refused",
                "does not exist",
                "undefinedtable",
                "no such table",
                "operationalerror",
                "could not translate host",
                "timeout",
            )
        )

    async def _persist_order(
        self,
        order: dict[str, Any],
        position: dict[str, Any] | None,
        journal: dict[str, Any] | None = None,
    ) -> bool:
        try:
            from database.session import get_session
            from repositories.fx_market_intel_repository import FxMarketIntelRepository

            async with get_session() as session:
                repo = FxMarketIntelRepository(session)
                await repo.upsert_paper_order(order)
                if position:
                    await repo.upsert_paper_position(position)
                if journal:
                    await repo.upsert_journal_entry(journal)
            return True
        except Exception as exc:
            if self._persist_soft_skip(exc):
                logger.warning("paper persist skipped (no durable store): %s", exc)
                return True
            logger.warning("paper persist failed: %s", exc)
            return False

    async def _persist_position(self, position: dict[str, Any], journal: dict[str, Any] | None = None) -> bool:
        try:
            from database.session import get_session
            from repositories.fx_market_intel_repository import FxMarketIntelRepository

            async with get_session() as session:
                repo = FxMarketIntelRepository(session)
                await repo.upsert_paper_position(position)
                if journal:
                    await repo.upsert_journal_entry(journal)
            return True
        except Exception as exc:
            if self._persist_soft_skip(exc):
                logger.warning("position/journal persist skipped (no durable store): %s", exc)
                return True
            logger.warning("position/journal persist failed: %s", exc)
            return False


_OPS: FxDeskOps | None = None


def get_fx_desk_ops() -> FxDeskOps:
    global _OPS
    if _OPS is None:
        _OPS = FxDeskOps()
    return _OPS


def reset_fx_desk_ops_for_tests() -> None:
    global _OPS
    _OPS = None

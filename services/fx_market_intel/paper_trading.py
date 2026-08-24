"""Paper trading simulation — NEVER places real broker/OTC orders."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

INITIAL_BALANCE_USD = 100_000.0
ORDER_STATUSES = {"DRAFT", "PENDING", "OPEN", "FILLED", "CLOSED", "CANCELLED"}


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(dt: datetime | None = None) -> str:
    return (dt or _now()).isoformat()


def assert_paper_only(payload: dict[str, Any]) -> None:
    if payload.get("paper") is not True:
        raise RuntimeError("Paper trade must be marked paper=True")
    if payload.get("trade_execution") is True:
        raise RuntimeError("Paper trading must not enable real trade_execution")
    if payload.get("broker_execution") is True:
        raise RuntimeError("Paper trading must not enable broker_execution")


def new_account(tenant_id: str) -> dict[str, Any]:
    return {
        "tenant_id": tenant_id or "default",
        "currency": "USD",
        "balance": INITIAL_BALANCE_USD,
        "equity": INITIAL_BALANCE_USD,
        "open_pnl": 0.0,
        "realized_pnl": 0.0,
        "win_rate": 0.0,
        "trades_count": 0,
        "wins": 0,
        "paper": True,
        "trade_execution": False,
        "label_ru": "Демо-счёт бумажной торговли",
    }


def validate_sl_tp_vs_side(
    *,
    side: str,
    entry: float,
    stop_loss: float | None,
    take_profit: float | None,
) -> dict[str, Any]:
    """Hard validation of SL/TP relative to entry for BUY/SELL."""
    side_u = (side or "BUY").upper()
    if entry <= 0:
        return {
            "ok": False,
            "error": "entry_unavailable",
            "message_ru": "Недостаточно данных для расчёта риска",
        }
    if stop_loss is not None:
        sl = float(stop_loss)
        if side_u == "BUY" and sl >= entry:
            return {
                "ok": False,
                "error": "invalid_stop_loss",
                "message_ru": "Stop Loss для BUY должен быть ниже цены входа",
            }
        if side_u == "SELL" and sl <= entry:
            return {
                "ok": False,
                "error": "invalid_stop_loss",
                "message_ru": "Stop Loss для SELL должен быть выше цены входа",
            }
    if take_profit is not None:
        tp = float(take_profit)
        if side_u == "BUY" and tp <= entry:
            return {
                "ok": False,
                "error": "invalid_take_profit",
                "message_ru": "Take Profit для BUY должен быть выше цены входа",
            }
        if side_u == "SELL" and tp >= entry:
            return {
                "ok": False,
                "error": "invalid_take_profit",
                "message_ru": "Take Profit для SELL должен быть ниже цены входа",
            }
    return {"ok": True}


def risk_preview(
    *,
    entry: float,
    stop_loss: float | None,
    take_profit: float | None,
    quantity: float,
    side: str,
    balance: float,
) -> dict[str, Any]:
    pot_loss = None
    pot_profit = None
    risk_pct = None
    reward_risk = None
    if stop_loss is not None and entry:
        pot_loss = round(abs(entry - float(stop_loss)) * quantity, 4)
        if balance > 0:
            risk_pct = round(100.0 * pot_loss / balance, 3)
    if take_profit is not None and entry:
        pot_profit = round(abs(float(take_profit) - entry) * quantity, 4)
    if pot_loss and pot_loss > 0 and pot_profit is not None:
        reward_risk = round(pot_profit / pot_loss, 3)
    return {
        "potential_loss": pot_loss,
        "potential_profit": pot_profit,
        "risk_pct": risk_pct,
        "reward_risk": reward_risk,
        "risk_usd": pot_loss,
        "rr": reward_risk,
    }


def validate_risk_agent(
    *,
    risk_settings: dict[str, Any] | None,
    preview: dict[str, Any],
    open_positions: int = 0,
) -> dict[str, Any]:
    """Soft Risk Agent checks for paper trading — warn by default, block only if strict."""
    settings = risk_settings or {}
    warnings: list[str] = []
    min_rr = settings.get("minimum_rr")
    if min_rr is not None and preview.get("reward_risk") is not None:
        if float(preview["reward_risk"]) < float(min_rr):
            warnings.append(
                f"Risk Agent: сделка ниже установленного минимального R/R ({preview['reward_risk']} < {min_rr})."
            )
    max_open = settings.get("max_open_positions")
    if max_open is not None and open_positions >= int(max_open):
        warnings.append(f"Risk Agent: достигнут лимит открытых позиций ({max_open}).")
    max_risk_pct = settings.get("max_risk_per_trade_pct")
    if max_risk_pct is not None and preview.get("risk_pct") is not None:
        if float(preview["risk_pct"]) > float(max_risk_pct):
            warnings.append(
                f"Risk Agent: риск {preview['risk_pct']}% выше max risk per trade ({max_risk_pct}%)."
            )
    strict = bool(settings.get("strict"))
    return {
        "ok": not (strict and warnings),
        "warnings": warnings,
        "strict": strict,
        "agent": "Risk Agent",
    }


def create_paper_order(
    *,
    tenant_id: str,
    instrument: str,
    side: str,
    order_type: str,
    quantity: float,
    limit_price: float | None = None,
    entry_price: float | None = None,
    stop_loss: float | None = None,
    take_profit: float | None = None,
    signal_id: str | None = None,
    analysis_run_id: str | None = None,
    agent_result_id: str | None = None,
    mark_price: float | None = None,
    notes: str = "",
    draft: bool = False,
) -> dict[str, Any]:
    side_u = side.upper()
    if side_u not in {"BUY", "SELL"}:
        raise ValueError("side must be BUY or SELL")
    ot = order_type.upper()
    if ot not in {"MARKET", "LIMIT"}:
        ot = "MARKET" if order_type.lower() == "market" else "LIMIT" if order_type.lower() == "limit" else order_type.upper()
    if ot not in {"MARKET", "LIMIT"}:
        raise ValueError("order_type must be MARKET or LIMIT")
    if quantity <= 0:
        raise ValueError("quantity must be > 0")
    if ot == "LIMIT" and limit_price is None:
        raise ValueError("limit_price required for LIMIT")

    order_id = f"po_{uuid.uuid4().hex[:12]}"
    if draft:
        status = "DRAFT"
        fill_price = None
        filled_at = None
    elif ot == "MARKET":
        if mark_price is None:
            status = "CANCELLED"
            fill_price = None
            filled_at = None
        else:
            status = "FILLED"
            fill_price = float(mark_price if entry_price is None else entry_price)
            filled_at = _iso()
    else:
        status = "PENDING"
        fill_price = None
        filled_at = None

    preview = risk_preview(
        entry=float(fill_price or limit_price or entry_price or mark_price or 0),
        stop_loss=stop_loss,
        take_profit=take_profit,
        quantity=quantity,
        side=side_u,
        balance=INITIAL_BALANCE_USD,
    )
    order = {
        "order_id": order_id,
        "tenant_id": tenant_id or "default",
        "instrument": instrument,
        "side": side_u,
        "order_type": ot,
        "quantity": float(quantity),
        "limit_price": float(limit_price) if limit_price is not None else None,
        "entry_price": float(entry_price) if entry_price is not None else fill_price,
        "stop_loss": float(stop_loss) if stop_loss is not None else None,
        "take_profit": float(take_profit) if take_profit is not None else None,
        "status": status,
        "fill_price": fill_price,
        "filled_at": filled_at,
        "signal_id": signal_id,
        "analysis_run_id": analysis_run_id,
        "agent_result_id": agent_result_id,
        "notes": notes,
        "created_at": _iso(),
        "risk": preview,
        "paper": True,
        "trade_execution": False,
        "broker_execution": False,
        "label_ru": "Бумажная сделка (симуляция)",
    }
    if status == "CANCELLED":
        order["message_ru"] = "Не удалось получить котировку " + str(instrument)
    assert_paper_only(order)
    position = open_position_from_order(order) if status == "FILLED" and fill_price is not None else None
    return {"order": order, "position": position}


def open_position_from_order(order: dict[str, Any]) -> dict[str, Any]:
    pos = {
        "position_id": f"pp_{uuid.uuid4().hex[:12]}",
        "tenant_id": order["tenant_id"],
        "order_id": order["order_id"],
        "instrument": order["instrument"],
        "side": order["side"],
        "quantity": order["quantity"],
        "entry_price": order["fill_price"],
        "current_price": order["fill_price"],
        "unrealized_pnl": 0.0,
        "stop_loss": order.get("stop_loss"),
        "take_profit": order.get("take_profit"),
        "status": "OPEN",
        "opened_at": order.get("filled_at") or _iso(),
        "closed_at": None,
        "exit_price": None,
        "pnl": None,
        "pnl_pips": None,
        "duration_sec": None,
        "signal_id": order.get("signal_id"),
        "analysis_run_id": order.get("analysis_run_id"),
        "agent_result_id": order.get("agent_result_id"),
        "close_reason": None,
        "paper": True,
        "trade_execution": False,
        "broker_execution": False,
        "label_ru": "Бумажная позиция",
    }
    assert_paper_only(pos)
    return pos


def unrealized_pnl(*, side: str, entry: float, mark: float, quantity: float) -> float:
    direction = 1.0 if side.upper() == "BUY" else -1.0
    return round((mark - entry) * direction * quantity, 6)


def pnl_for_close(*, side: str, entry: float, exit_price: float, quantity: float) -> dict[str, float]:
    direction = 1.0 if side.upper() == "BUY" else -1.0
    move = (exit_price - entry) * direction
    pips = move / 0.0001 if abs(entry) < 10 else move / 0.01
    return {"pnl": round(move * quantity, 6), "pnl_pips": round(pips, 2)}


def try_fill_limit(order: dict[str, Any], mark_price: float) -> dict[str, Any] | None:
    if order.get("status") != "PENDING" or order.get("order_type") != "LIMIT":
        # backward compat lowercase
        if not (order.get("status") in {"PENDING", "pending"} and str(order.get("order_type", "")).upper() == "LIMIT"):
            return None
    lim = float(order["limit_price"])
    side = order["side"]
    hit = (side == "BUY" and mark_price <= lim) or (side == "SELL" and mark_price >= lim)
    if not hit:
        return None
    order = {
        **order,
        "status": "FILLED",
        "fill_price": mark_price,
        "entry_price": mark_price,
        "filled_at": _iso(),
    }
    assert_paper_only(order)
    return {"order": order, "position": open_position_from_order(order)}


def cancel_pending(order: dict[str, Any]) -> dict[str, Any]:
    if order.get("status") not in {"PENDING", "DRAFT", "pending"}:
        raise ValueError("only pending/draft can be cancelled")
    out = {**order, "status": "CANCELLED"}
    assert_paper_only(out)
    return out


def check_sl_tp(position: dict[str, Any], mark_price: float) -> dict[str, Any] | None:
    if str(position.get("status", "")).upper() != "OPEN":
        return None
    side = position["side"]
    sl = position.get("stop_loss")
    tp = position.get("take_profit")
    reason = None
    if sl is not None:
        if side == "BUY" and mark_price <= float(sl):
            reason = "stop_loss"
        if side == "SELL" and mark_price >= float(sl):
            reason = "stop_loss"
    if tp is not None and reason is None:
        if side == "BUY" and mark_price >= float(tp):
            reason = "take_profit"
        if side == "SELL" and mark_price <= float(tp):
            reason = "take_profit"
    if not reason:
        return None
    return close_position(position, exit_price=mark_price, reason=reason)


def mark_position(position: dict[str, Any], mark_price: float) -> dict[str, Any]:
    if str(position.get("status", "")).upper() != "OPEN":
        return position
    upnl = unrealized_pnl(
        side=str(position["side"]),
        entry=float(position["entry_price"]),
        mark=mark_price,
        quantity=float(position["quantity"]),
    )
    return {**position, "current_price": mark_price, "unrealized_pnl": upnl}


def close_position(
    position: dict[str, Any],
    *,
    exit_price: float,
    reason: str = "manual",
) -> dict[str, Any]:
    if str(position.get("status", "")).upper() != "OPEN":
        raise ValueError("position is not open")
    entry = float(position["entry_price"])
    metrics = pnl_for_close(
        side=str(position["side"]),
        entry=entry,
        exit_price=float(exit_price),
        quantity=float(position["quantity"]),
    )
    opened = datetime.fromisoformat(str(position["opened_at"]).replace("Z", "+00:00"))
    closed_at = _now()
    duration = int((closed_at - opened).total_seconds())
    closed = {
        **position,
        "status": "CLOSED",
        "exit_price": float(exit_price),
        "current_price": float(exit_price),
        "closed_at": _iso(closed_at),
        "pnl": metrics["pnl"],
        "realized_pnl": metrics["pnl"],
        "unrealized_pnl": 0.0,
        "pnl_pips": metrics["pnl_pips"],
        "duration_sec": duration,
        "close_reason": reason,
        "result": "win" if metrics["pnl"] > 0 else "loss" if metrics["pnl"] < 0 else "flat",
        "paper": True,
        "trade_execution": False,
        "broker_execution": False,
    }
    assert_paper_only(closed)
    return closed


def account_snapshot(account: dict[str, Any], positions: list[dict[str, Any]], journal: list[dict[str, Any]]) -> dict[str, Any]:
    open_pos = [p for p in positions if str(p.get("status", "")).upper() == "OPEN"]
    open_pnl = round(sum(float(p.get("unrealized_pnl") or 0) for p in open_pos), 4)
    realized = round(float(account.get("realized_pnl") or 0), 4)
    # Prefer sum of journal if present
    if journal:
        realized = round(sum(float(j.get("pnl") or 0) for j in journal), 4)
    wins = sum(1 for j in journal if float(j.get("pnl") or 0) > 0)
    trades = len(journal)
    balance = float(account.get("balance") or INITIAL_BALANCE_USD)
    # equity = cash remaining notionally balance + open pnl (demo: balance stays initial +/- realized)
    equity = round(INITIAL_BALANCE_USD + realized + open_pnl, 4)
    cash = round(INITIAL_BALANCE_USD + realized, 4)
    return {
        **account,
        "balance": cash,
        "equity": equity,
        "open_pnl": open_pnl,
        "realized_pnl": realized,
        "open_positions": len(open_pos),
        "trades_count": trades,
        "wins": wins,
        "win_rate": round(100.0 * wins / trades, 2) if trades else 0.0,
        "paper": True,
        "trade_execution": False,
    }

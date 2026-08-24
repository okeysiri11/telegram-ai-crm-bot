"""HTTP handlers — FX market intelligence (Sprint 50.0 / 50.1)."""

from __future__ import annotations

from aiohttp import web

from applications.crypto_enterprise.api.middleware import json_response
from services.fx_market_intel import get_fx_market_intel


async def _read_json(request: web.Request) -> dict:
    try:
        data = await request.json()
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _tenant(request: web.Request, body: dict | None = None) -> str:
    body = body or {}
    return str(
        body.get("tenant_id")
        or request.rel_url.query.get("tenant_id")
        or request.headers.get("X-Tenant-Id")
        or "default"
    )


async def fx_intel_health_handler(request: web.Request) -> web.Response:
    svc = get_fx_market_intel()
    health = await svc.connection_health()
    return json_response({"status": "ok", "health": health})


async def fx_intel_snapshot_handler(request: web.Request) -> web.Response:
    svc = get_fx_market_intel()
    tenant = _tenant(request)
    return json_response(await svc.desk_snapshot(tenant_id=tenant))


async def fx_intel_quote_handler(request: web.Request) -> web.Response:
    svc = get_fx_market_intel()
    body = await _read_json(request) if request.method == "POST" else {}
    symbol = body.get("symbol") or request.rel_url.query.get("symbol") or "EUR/USD"
    return json_response(await svc.quote(str(symbol)))


async def fx_intel_candles_handler(request: web.Request) -> web.Response:
    svc = get_fx_market_intel()
    body = await _read_json(request) if request.method == "POST" else {}
    symbol = body.get("symbol") or request.rel_url.query.get("symbol") or "EUR/USD"
    timeframe = body.get("timeframe") or request.rel_url.query.get("timeframe") or "1H"
    return json_response(await svc.candles(str(symbol), str(timeframe)))


async def fx_intel_run_handler(request: web.Request) -> web.Response:
    svc = get_fx_market_intel()
    body = await _read_json(request)
    tenant = _tenant(request, body)
    specialist = str(body.get("specialist_id") or body.get("agent") or body.get("preset_id") or "chief")
    timeframe = str(body.get("timeframe") or "1H")
    preset = body.get("preset_id")
    try:
        if preset or specialist in {"morning", "evening", "pre_trade", "pre_europe", "pre_us", "event"}:
            result = await svc.run_full_analysis(
                preset_id=str(preset or specialist),
                tenant_id=tenant,
                timeframe=timeframe,
                user_id=str(body.get("user_id") or "") or None,
            )
        else:
            result = await svc.run_specialist(
                specialist_id=specialist,
                tenant_id=tenant,
                bars=body.get("bars") if isinstance(body.get("bars"), list) else [],
                timeframe=timeframe,
            )
    except Exception as exc:
        return json_response({"ok": False, "error": str(exc)}, status=500)
    return json_response(result, status=201 if result.get("ok") else 400)


async def fx_intel_signals_handler(request: web.Request) -> web.Response:
    svc = get_fx_market_intel()
    tenant = _tenant(request)
    return json_response({"items": await svc.list_signals(tenant), "analytics_only": True})


async def fx_intel_news_handler(request: web.Request) -> web.Response:
    svc = get_fx_market_intel()
    if request.method == "POST":
        body = await _read_json(request)
        if body.get("action") == "ingest":
            articles = body.get("articles") if isinstance(body.get("articles"), list) else []
            return json_response(svc.ingest_news(articles), status=201)
    filt = request.rel_url.query.get("filter") or "Все"
    return json_response(await svc.news_feed(["EUR/USD", "DXY"], filter_key=str(filt)))


async def fx_intel_macro_handler(request: web.Request) -> web.Response:
    svc = get_fx_market_intel()
    return json_response(await svc.macro_calendar())


async def fx_intel_memory_handler(request: web.Request) -> web.Response:
    svc = get_fx_market_intel()
    tenant = _tenant(request)
    return json_response(await svc.memory(tenant))


async def fx_intel_history_handler(request: web.Request) -> web.Response:
    svc = get_fx_market_intel()
    tenant = _tenant(request)
    run_id = request.match_info.get("run_id") or request.rel_url.query.get("run_id")
    if run_id:
        return json_response(await svc.history_detail(str(run_id), tenant))
    return json_response(await svc.history(tenant))


async def fx_intel_technical_handler(request: web.Request) -> web.Response:
    svc = get_fx_market_intel()
    body = await _read_json(request)
    if body.get("live") or body.get("symbol"):
        return json_response(
            await svc.technical_live(
                str(body.get("symbol") or "EUR/USD"),
                str(body.get("timeframe") or "1H"),
            )
        )
    bars = body.get("bars") if isinstance(body.get("bars"), list) else []
    return json_response(svc.technical(bars))


async def fx_intel_correlation_handler(request: web.Request) -> web.Response:
    svc = get_fx_market_intel()
    body = await _read_json(request)
    e = [float(x) for x in (body.get("eurusd_closes") or [])]
    d = [float(x) for x in (body.get("dxy_closes") or [])]
    if not e and not d:
        eurusd = await svc.candles("EUR/USD", str(body.get("timeframe") or "1H"))
        dxy = await svc.candles("DXY", str(body.get("timeframe") or "1H"))
        e = [b["c"] for b in (eurusd.get("bars") or [])[-60:]]
        d = [b["c"] for b in (dxy.get("bars") or [])[-60:]]
    return json_response(svc.correlation(e, d))



async def fx_intel_paper_handler(request: web.Request) -> web.Response:
    """Paper trading simulation endpoints — never real execution."""
    from services.fx_market_intel.desk_ops import get_fx_desk_ops

    ops = get_fx_desk_ops()
    body = await _read_json(request) if request.method == "POST" else {}
    tenant = _tenant(request, body)
    action = str(body.get("action") or request.rel_url.query.get("action") or "list")
    if request.method == "GET" or action == "list":
        await ops.ensure_hydrated(tenant)
        await ops.refresh_paper(tenant)
        return json_response(
            {
                "account": ops.get_account(tenant),
                "orders": ops.list_orders(tenant),
                "positions": ops.list_positions(tenant),
                "journal": ops.list_journal(tenant),
                "paper": True,
                "trade_execution": False,
                "message_ru": "Бумажная торговля (симуляция)",
                "sl_tp_auto_trigger": {
                    "mode": getattr(ops, "sl_tp_auto_trigger_mode", "on_refresh"),
                    "background_deferred": getattr(ops, "sl_tp_background_deferred", True),
                },
            }
        )
    if action == "place":
        try:
            result = await ops.place_paper_order(tenant_id=tenant, body=body)
        except Exception as exc:
            return json_response(
                {"ok": False, "error": str(exc), "message_ru": str(exc), "paper": True, "trade_execution": False},
                status=400,
            )
        if result.get("ok") is False:
            return json_response({**result, "paper": True, "trade_execution": False}, status=400)
        return json_response({"ok": True, **result, "paper": True, "trade_execution": False}, status=201)
    if action == "close":
        result = await ops.close_paper_position(
            tenant_id=tenant,
            position_id=str(body.get("position_id") or ""),
            notes=str(body.get("notes") or ""),
        )
        return json_response(result, status=200 if result.get("ok") else 400)
    if action == "cancel":
        result = await ops.cancel_paper_order(
            tenant_id=tenant,
            order_id=str(body.get("order_id") or ""),
        )
        return json_response(result, status=200 if result.get("ok") else 400)
    if action == "risk_preview":
        from services.fx_market_intel.paper_trading import INITIAL_BALANCE_USD, risk_preview, validate_risk_agent

        entry = float(body.get("entry_price") or body.get("limit_price") or 0)
        mark = await ops._mark(str(body.get("instrument") or "EUR/USD"))
        if entry <= 0 and mark is not None:
            entry = float(mark)
        preview = risk_preview(
            entry=entry,
            stop_loss=float(body["stop_loss"]) if body.get("stop_loss") is not None else None,
            take_profit=float(body["take_profit"]) if body.get("take_profit") is not None else None,
            quantity=float(body.get("quantity") or body.get("position_size") or 1),
            side=str(body.get("side") or "BUY"),
            balance=float((ops.get_account(tenant) or {}).get("balance") or INITIAL_BALANCE_USD),
        )
        risk_settings = body.get("risk_settings") if isinstance(body.get("risk_settings"), dict) else {}
        check = validate_risk_agent(risk_settings=risk_settings, preview=preview)
        return json_response({"ok": True, "risk": preview, "entry": entry, "mark": mark, "risk_warnings": check.get("warnings") or [], "paper": True})
    if action == "refresh":
        return json_response(await ops.refresh_paper(tenant))
    return json_response({"ok": False, "error": "unknown_action"}, status=400)


async def fx_intel_journal_handler(request: web.Request) -> web.Response:
    from services.fx_market_intel.desk_ops import get_fx_desk_ops

    ops = get_fx_desk_ops()
    tenant = _tenant(request)
    await ops.ensure_hydrated(tenant)
    return json_response({"items": ops.list_journal(tenant), "training_enabled": False, "paper": True})


async def fx_intel_signal_create_handler(request: web.Request) -> web.Response:
    from services.fx_market_intel.desk_ops import get_fx_desk_ops
    from services.fx_market_intel.signals import assert_no_trade_execution

    ops = get_fx_desk_ops()
    body = await _read_json(request)
    tenant = _tenant(request, body)
    # Build price trigger from form fields if provided
    price_trigger = body.get("price_trigger") if isinstance(body.get("price_trigger"), dict) else None
    if price_trigger is None and body.get("condition") and body.get("value") is not None:
        price_trigger = {
            "enabled": True,
            "price": float(body.get("value")),
            "direction": str(body.get("condition") or "cross"),
        }
    sig = await ops.create_manual_signal(
        tenant_id=tenant,
        instrument=str(body.get("instrument") or "EUR/USD"),
        signal=str(body.get("signal") or body.get("bias") or "WAIT"),
        timeframe=str(body.get("timeframe") or "1H"),
        confidence=float(body.get("confidence") or 0.5),
        reasons=body.get("reasons") if isinstance(body.get("reasons"), list) else [str(body.get("title") or "С графика / вручную")],
        analysis_run_id=body.get("analysis_run_id"),
        price_trigger=price_trigger,
        source=str(body.get("source") or "manual"),
    )
    # Enrich form fields
    sig["title"] = str(body.get("title") or sig.get("title") or f"Сигнал {sig.get('instrument')}")
    sig["kind"] = str(body.get("kind") or body.get("type") or "price_alert")
    sig["sound_profile"] = str(body.get("sound_profile") or body.get("sound") or "standard")
    sig["notification_channel"] = str(body.get("notification_channel") or "in_app")
    sig["active"] = bool(body.get("active", True))
    sig["enabled"] = sig["active"]
    sig["lifecycle"] = "ACTIVE" if sig["active"] else "DISABLED"
    sig["expires_at"] = body.get("expires") or body.get("expires_at") or sig.get("expires_at")
    sig["cooldown_sec"] = int(body.get("cooldown") or body.get("cooldown_sec") or 0)
    if body.get("condition"):
        sig["condition"] = str(body.get("condition"))
    if body.get("value") is not None:
        sig["value"] = body.get("value")
    assert_no_trade_execution(sig)
    return json_response({"ok": True, "signal": sig, "analytics_only": True, "trade_execution": False}, status=201)


async def fx_intel_links_handler(request: web.Request) -> web.Response:
    from services.fx_market_intel.desk_ops import get_fx_desk_ops

    ops = get_fx_desk_ops()
    tenant = _tenant(request)
    return json_response(
        ops.cross_links(
            tenant_id=tenant,
            signal_id=request.rel_url.query.get("signal_id"),
            analysis_run_id=request.rel_url.query.get("run_id") or request.rel_url.query.get("analysis_run_id"),
        )
    )


async def fx_intel_notifications_handler(request: web.Request) -> web.Response:
    from services.fx_market_intel.desk_ops import get_fx_desk_ops

    ops = get_fx_desk_ops()
    body = await _read_json(request) if request.method == "POST" else {}
    tenant = _tenant(request, body)
    if request.method == "GET":
        return json_response({"items": ops.list_notifications(tenant), "channel": "in_app"})
    action = str(body.get("action") or "ack")
    result = ops.act_notification(
        tenant,
        str(body.get("notification_id") or ""),
        action,
    )
    return json_response(result, status=200 if result.get("ok") else 404)


async def fx_intel_calendar_handler(request: web.Request) -> web.Response:
    from services.fx_market_intel.desk_ops import get_fx_desk_ops

    ops = get_fx_desk_ops()
    body = await _read_json(request) if request.method == "POST" else {}
    tenant = _tenant(request, body)
    if request.method == "POST" and str(body.get("action") or "") == "create":
        ev = ops.add_manual_event(tenant, body)
        return json_response({"ok": True, "event": ev}, status=201)
    filters = None
    raw = request.rel_url.query.get("filters")
    if isinstance(body.get("filters"), dict):
        filters = {str(k): bool(v) for k, v in body["filters"].items()}
    elif raw:
        # filters=macro,news,signal
        enabled = {x.strip(): True for x in raw.split(",") if x.strip()}
        filters = {
            "macro": enabled.get("macro", False) or "macro" in enabled,
            "news": enabled.get("news", False) or "news" in enabled,
            "analysis": enabled.get("analysis", False) or "analysis" in enabled,
            "agent": enabled.get("agent", False) or "agent" in enabled,
            "signal": enabled.get("signal", False) or "signal" in enabled,
            "session": enabled.get("session", False) or "session" in enabled,
            "paper": enabled.get("paper", False) or "paper" in enabled,
            "manual": enabled.get("manual", True),
        }
        # if query provided, only those true — but empty means all on via default
        if not enabled:
            filters = None
    return json_response(await ops.calendar_bundle(tenant, filters))


async def fx_intel_schedule_handler(request: web.Request) -> web.Response:
    """Timezone-aware schedule listing + upsert (enable/time/timezone)."""
    from services.fx_market_intel.schedule import list_fx_intel_schedule, upsert_schedule

    body = await _read_json(request) if request.method == "POST" else {}
    tenant = _tenant(request, body)
    if request.method == "POST":
        preset = str(body.get("preset_id") or body.get("id") or "")
        try:
            cfg = upsert_schedule(
                tenant,
                preset,
                enabled=body.get("enabled") if "enabled" in body else None,
                hour=int(body["hour"]) if body.get("hour") is not None else None,
                minute=int(body["minute"]) if body.get("minute") is not None else None,
                timezone_name=str(body.get("timezone") or body.get("timezone_name") or "") or None,
            )
        except Exception as exc:
            return json_response({"ok": False, "error": str(exc)}, status=400)
        bundle = await list_fx_intel_schedule(tenant)
        return json_response({"ok": True, "config": cfg, **bundle})
    return json_response(await list_fx_intel_schedule(tenant))


async def fx_intel_signal_patch_handler(request: web.Request) -> web.Response:
    """Enable/disable signal lifecycle without trade execution."""
    from services.fx_market_intel import get_fx_market_intel
    from services.fx_market_intel.desk_ops import get_fx_desk_ops
    from services.fx_market_intel.signals import assert_no_trade_execution

    body = await _read_json(request)
    tenant = _tenant(request, body)
    signal_id = str(body.get("signal_id") or request.match_info.get("signal_id") or "")
    enabled = body.get("enabled")
    action = str(body.get("action") or "")
    if enabled is True or action in {"enable", "включить"}:
        lifecycle = "ACTIVE"
    elif enabled is False or action in {"disable", "отключить"}:
        lifecycle = "DISABLED"
    else:
        lifecycle = str(body.get("lifecycle") or "ACTIVE")
    svc = get_fx_market_intel()
    ops = get_fx_desk_ops()
    updated = None
    for s in await svc.list_signals(tenant):
        if s.get("signal_id") == signal_id:
            s["lifecycle"] = lifecycle
            s["enabled"] = lifecycle == "ACTIVE"
            assert_no_trade_execution(s)
            updated = s
            break
    if updated is None:
        for s in ops._manual_signals.get(tenant, []):
            if s.get("signal_id") == signal_id:
                s["lifecycle"] = lifecycle
                s["enabled"] = lifecycle == "ACTIVE"
                updated = s
                break
    if not updated:
        return json_response({"ok": False, "error": "signal_not_found"}, status=404)
    return json_response({"ok": True, "signal": updated, "analytics_only": True, "trade_execution": False})

"""Live provider API calls. CONNECTED only after a successful real (or injected) response."""

from __future__ import annotations

import json
import os
import smtplib
import ssl
from email.message import EmailMessage
from typing import Any, Callable

from services.recruiting_ops.provider_contract import NOT_CONFIGURED, adapter_result
from services.recruiting_ops.provider_http import provider_request
from services.recruiting_ops.provider_oauth import google_ads_version, graph_version, refresh_google_access_token, tiktok_version
from services.recruiting_ops.secret_store import get_secret_store

SmtpFactory = Callable[..., Any]
_SMTP_FACTORY: SmtpFactory | None = None


def set_smtp_factory(factory: SmtpFactory | None) -> None:
    global _SMTP_FACTORY
    _SMTP_FACTORY = factory


def _txt(value: Any) -> str:
    return str(value or "").strip()


def _store():
    return get_secret_store()


def _secret(provider: str, field: str, *env_names: str) -> str:
    value = _store().get(provider, field)
    if value:
        return value
    for name in env_names:
        found = _txt(os.getenv(name))
        if found:
            return found
    return ""


def _public(provider: str, field: str, *env_names: str) -> str:
    value = _txt(_store().get(provider, field))
    if value:
        return value
    for name in env_names:
        found = _txt(os.getenv(name))
        if found:
            return found
    return ""


def _not_configured(provider: str) -> dict[str, Any]:
    return adapter_result(
        ok=False,
        error=NOT_CONFIGURED,
        status="NOT_CONFIGURED",
        connected=False,
        mode="LIVE",
        provider=provider,
        message_ru="Учётные данные не заданы.",
    )


def _from_http(provider: str, result: dict[str, Any], *, identity: dict[str, Any] | None = None, items: list | None = None, metrics: dict | None = None) -> dict[str, Any]:
    ok = bool(result.get("ok"))
    return adapter_result(
        ok=ok,
        error=None if ok else result.get("error"),
        error_code=None if ok else result.get("error_code"),
        status="CONNECTED" if ok else "ERROR",
        connected=ok,
        live_verified=ok and not result.get("mocked_http"),
        mocked_http=bool(result.get("mocked_http")),
        mode="LIVE",
        provider=provider,
        latency_ms=result.get("latency_ms"),
        identity=identity,
        items=items if items is not None else [],
        metrics=metrics,
        account_id=(identity or {}).get("id") or (identity or {}).get("account_id"),
        message_ru="Проверка провайдера успешна." if ok else result.get("message_ru"),
        request=result.get("request"),
    )


def meta_act_id() -> str:
    raw = _public("meta", "ad_account_id", "META_ADS_ACCOUNT_ID")
    if not raw:
        return ""
    return raw if raw.startswith("act_") else f"act_{raw}"


def live_health(provider: str) -> dict[str, Any]:
    key = _txt(provider).lower()
    if key == "meta":
        token = _secret("meta", "access_token", "META_ADS_ACCESS_TOKEN")
        if not token:
            return _not_configured(key)
        result = provider_request(
            "GET",
            f"https://graph.facebook.com/{graph_version()}/me",
            query={"fields": "id,name", "access_token": token},
        )
        data = result.get("json") if isinstance(result.get("json"), dict) else {}
        identity = {"id": data.get("id"), "name": data.get("name")} if result.get("ok") else None
        account = meta_act_id()
        if result.get("ok") and account:
            extra = provider_request(
                "GET",
                f"https://graph.facebook.com/{graph_version()}/{account}",
                query={"fields": "id,name,account_status", "access_token": token},
            )
            if extra.get("ok"):
                acc = extra.get("json") if isinstance(extra.get("json"), dict) else {}
                identity = {**(identity or {}), "account_id": acc.get("id"), "account_name": acc.get("name")}
            else:
                return _from_http(key, extra, identity=identity)
        return _from_http(key, result, identity=identity)
    if key == "google":
        developer = _secret("google", "developer_token", "GOOGLE_ADS_DEVELOPER_TOKEN")
        refresh = _secret("google", "refresh_token", "GOOGLE_ADS_REFRESH_TOKEN")
        customer = _public("google", "customer_id", "GOOGLE_ADS_CUSTOMER_ID").replace("-", "")
        if not developer or not refresh:
            return _not_configured(key)
        token_res = refresh_google_access_token()
        token = _txt(token_res.get("access_token"))
        if not token:
            return adapter_result(
                ok=False,
                error=token_res.get("error") or "AUTH_ERROR",
                status="ERROR" if refresh else "NOT_CONFIGURED",
                connected=False,
                mode="LIVE",
                message_ru=token_res.get("message_ru") or "Не удалось обновить Google access token.",
            )
        if not customer:
            return adapter_result(ok=False, error="INVALID_ACCOUNT", status="ERROR", connected=False, mode="LIVE", message_ru="Не задан Google customer ID.")
        login = _public("google", "manager_id", "GOOGLE_ADS_LOGIN_CUSTOMER_ID").replace("-", "")
        headers = {"Authorization": f"Bearer {token}", "developer-token": developer, "Content-Type": "application/json"}
        if login:
            headers["login-customer-id"] = login
        result = provider_request(
            "POST",
            f"https://googleads.googleapis.com/{google_ads_version()}/customers/{customer}/googleAds:search",
            headers=headers,
            json_body={"query": "SELECT customer.id, customer.descriptive_name FROM customer LIMIT 1"},
        )
        data = result.get("json") if isinstance(result.get("json"), dict) else {}
        rows = data.get("results") if isinstance(data.get("results"), list) else []
        first = rows[0].get("customer") if rows and isinstance(rows[0], dict) else {}
        identity = {"id": first.get("id") or customer, "name": first.get("descriptiveName") or first.get("descriptive_name")}
        return _from_http(key, result, identity=identity)
    if key == "tiktok":
        token = _secret("tiktok", "access_token", "TIKTOK_ADS_ACCESS_TOKEN")
        advertiser = _public("tiktok", "advertiser_id", "TIKTOK_ADS_ADVERTISER_ID")
        if not token:
            return _not_configured(key)
        if not advertiser:
            return adapter_result(ok=False, error="INVALID_ACCOUNT", status="ERROR", connected=False, mode="LIVE", message_ru="Не задан advertiser ID.")
        result = provider_request(
            "GET",
            f"https://business-api.tiktok.com/open_api/{tiktok_version()}/advertiser/info/",
            headers={"Access-Token": token},
            query={"advertiser_ids": json.dumps([advertiser])},
        )
        data = result.get("json") if isinstance(result.get("json"), dict) else {}
        code_ok = data.get("code") in (0, "0", None) or result.get("ok")
        if data.get("code") not in (None, 0, "0") and int(data.get("code") or 0) != 0:
            result = {**result, "ok": False, "error": result.get("error") or "UNKNOWN_PROVIDER_ERROR"}
        items = data.get("data", {}).get("list") if isinstance(data.get("data"), dict) else []
        first = items[0] if isinstance(items, list) and items else {}
        identity = {"id": first.get("advertiser_id") or advertiser, "name": first.get("name")}
        packed = {**result, "ok": bool(result.get("ok") and code_ok)}
        return _from_http(key, packed, identity=identity)
    if key == "telegram":
        token = _secret("telegram", "bot_token", "VANGUARD_TELEGRAM_BOT_TOKEN")
        if not token:
            return _not_configured(key)
        result = provider_request("GET", f"https://api.telegram.org/bot{token}/getMe")
        data = result.get("json") if isinstance(result.get("json"), dict) else {}
        ok = bool(result.get("ok") and data.get("ok"))
        inner = data.get("result") if isinstance(data.get("result"), dict) else {}
        identity = {"id": inner.get("id"), "username": inner.get("username"), "name": inner.get("first_name")}
        packed = {**result, "ok": ok}
        return _from_http(key, packed, identity=identity)
    if key == "whatsapp":
        token = _secret("whatsapp", "access_token", "WHATSAPP_TOKEN")
        phone = _public("whatsapp", "phone_number_id", "WHATSAPP_PHONE_NUMBER_ID")
        if not token:
            return _not_configured(key)
        if not phone:
            return adapter_result(ok=False, error="INVALID_ACCOUNT", status="ERROR", connected=False, mode="LIVE", message_ru="Не задан phone number id.")
        result = provider_request(
            "GET",
            f"https://graph.facebook.com/{graph_version()}/{phone}",
            query={"fields": "id,display_phone_number,verified_name", "access_token": token},
        )
        data = result.get("json") if isinstance(result.get("json"), dict) else {}
        identity = {"id": data.get("id") or phone, "name": data.get("verified_name"), "phone": data.get("display_phone_number")}
        return _from_http(key, result, identity=identity)
    if key == "email":
        return smtp_health()
    return _not_configured(key)


def smtp_settings() -> dict[str, Any]:
    port_raw = _public("email", "smtp_port", "SMTP_PORT") or "587"
    try:
        port = int(port_raw)
    except ValueError:
        port = 587
    tls_mode = (_public("email", "tls_mode", "SMTP_TLS_MODE") or "starttls").lower()
    return {
        "host": _public("email", "smtp_host", "SMTP_HOST"),
        "port": port,
        "user": _public("email", "smtp_user", "SMTP_USER"),
        "password": _secret("email", "smtp_password", "SMTP_PASSWORD"),
        "sender": _public("email", "email_from", "EMAIL_FROM"),
        "sender_name": _public("email", "sender_name", "EMAIL_FROM_NAME"),
        "tls_mode": tls_mode,
    }


def smtp_health() -> dict[str, Any]:
    cfg = smtp_settings()
    if not cfg["host"] or not cfg["sender"]:
        return _not_configured("email")
    factory = _SMTP_FACTORY
    try:
        if factory:
            client = factory(cfg["host"], cfg["port"])
        elif cfg["tls_mode"] == "ssl":
            client = smtplib.SMTP_SSL(cfg["host"], cfg["port"], timeout=10)
        else:
            client = smtplib.SMTP(cfg["host"], cfg["port"], timeout=10)
        with client:
            client.ehlo()
            if cfg["tls_mode"] != "ssl" and cfg["tls_mode"] != "none":
                context = ssl.create_default_context()
                client.starttls(context=context)
                client.ehlo()
            if cfg["user"]:
                client.login(cfg["user"], cfg["password"] or "")
        return adapter_result(
            ok=True,
            status="CONNECTED",
            connected=True,
            live_verified=factory is None,
            mocked_http=factory is not None,
            mode="LIVE",
            provider="email",
            identity={"id": cfg["sender"], "name": cfg["sender_name"] or cfg["sender"]},
            message_ru="SMTP-соединение успешно.",
        )
    except Exception as exc:
        return adapter_result(
            ok=False,
            error="PROVIDER_UNAVAILABLE",
            status="ERROR",
            connected=False,
            mode="LIVE",
            provider="email",
            message_ru="SMTP недоступен.",
            last_error=type(exc).__name__,
        )


def live_list_accounts(provider: str) -> dict[str, Any]:
    key = _txt(provider).lower()
    health = live_health(key)
    if not health.get("ok"):
        return {**health, "items": []}
    if key == "meta":
        token = _secret("meta", "access_token", "META_ADS_ACCESS_TOKEN")
        result = provider_request(
            "GET",
            f"https://graph.facebook.com/{graph_version()}/me/adaccounts",
            query={"fields": "id,name,account_id,currency", "access_token": token},
        )
        data = result.get("json") if isinstance(result.get("json"), dict) else {}
        items = data.get("data") if isinstance(data.get("data"), list) else []
        return _from_http(key, result, identity=health.get("identity"), items=items)
    if key == "google":
        return {**health, "items": [health.get("identity") or {}]}
    if key == "tiktok":
        return {**health, "items": [health.get("identity") or {}]}
    return {**health, "items": [health.get("identity") or {}]}


def live_list_campaigns(provider: str, *, cursor: str | None = None) -> dict[str, Any]:
    key = _txt(provider).lower()
    health = live_health(key)
    if not health.get("ok"):
        return {**health, "items": [], "cursor": None}
    if key == "meta":
        token = _secret("meta", "access_token", "META_ADS_ACCESS_TOKEN")
        account = meta_act_id()
        if not account:
            return adapter_result(ok=False, error="INVALID_ACCOUNT", items=[], status="ERROR", mode="LIVE", message_ru="Нет Ad Account ID.")
        query = {"fields": "id,name,status,daily_budget,lifetime_budget,start_time,stop_time,objective", "access_token": token, "limit": 50}
        url = cursor or f"https://graph.facebook.com/{graph_version()}/{account}/campaigns"
        result = provider_request("GET", url, query=None if cursor else query)
        data = result.get("json") if isinstance(result.get("json"), dict) else {}
        paging = data.get("paging") if isinstance(data.get("paging"), dict) else {}
        return {**_from_http(key, result, items=data.get("data") if isinstance(data.get("data"), list) else []), "cursor": (paging.get("next") or None)}
    if key == "google":
        developer = _secret("google", "developer_token", "GOOGLE_ADS_DEVELOPER_TOKEN")
        token_res = refresh_google_access_token()
        token = _txt(token_res.get("access_token"))
        customer = _public("google", "customer_id", "GOOGLE_ADS_CUSTOMER_ID").replace("-", "")
        login = _public("google", "manager_id", "GOOGLE_ADS_LOGIN_CUSTOMER_ID").replace("-", "")
        headers = {"Authorization": f"Bearer {token}", "developer-token": developer, "Content-Type": "application/json"}
        if login:
            headers["login-customer-id"] = login
        body: dict[str, Any] = {
            "query": "SELECT campaign.id, campaign.name, campaign.status, campaign_budget.amount_micros, campaign.start_date, campaign.end_date FROM campaign LIMIT 50"
        }
        if cursor:
            body["pageToken"] = cursor
        result = provider_request(
            "POST",
            f"https://googleads.googleapis.com/{google_ads_version()}/customers/{customer}/googleAds:search",
            headers=headers,
            json_body=body,
        )
        data = result.get("json") if isinstance(result.get("json"), dict) else {}
        rows = []
        for row in data.get("results") or []:
            camp = row.get("campaign") if isinstance(row, dict) else {}
            budget = row.get("campaignBudget") or row.get("campaign_budget") or {}
            micros = budget.get("amountMicros") or budget.get("amount_micros")
            rows.append(
                {
                    "id": camp.get("id"),
                    "name": camp.get("name"),
                    "status": camp.get("status"),
                    "budget": int(micros) / 1_000_000 if micros else None,
                    "start_at": camp.get("startDate") or camp.get("start_date"),
                    "end_at": camp.get("endDate") or camp.get("end_date"),
                }
            )
        return {**_from_http(key, result, items=rows), "cursor": data.get("nextPageToken")}
    if key == "tiktok":
        token = _secret("tiktok", "access_token", "TIKTOK_ADS_ACCESS_TOKEN")
        advertiser = _public("tiktok", "advertiser_id", "TIKTOK_ADS_ADVERTISER_ID")
        result = provider_request(
            "GET",
            f"https://business-api.tiktok.com/open_api/{tiktok_version()}/campaign/get/",
            headers={"Access-Token": token},
            query={"advertiser_id": advertiser, "page": cursor or 1, "page_size": 50},
        )
        data = result.get("json") if isinstance(result.get("json"), dict) else {}
        inner = data.get("data") if isinstance(data.get("data"), dict) else {}
        items = inner.get("list") if isinstance(inner.get("list"), list) else []
        page = inner.get("page_info") if isinstance(inner.get("page_info"), dict) else {}
        next_page = None
        if page.get("page") and page.get("total_page") and int(page.get("page") or 0) < int(page.get("total_page") or 0):
            next_page = str(int(page["page"]) + 1)
        return {**_from_http(key, result, items=items), "cursor": next_page}
    return {**health, "items": [], "cursor": None}


def live_fetch_metrics(provider: str) -> dict[str, Any]:
    key = _txt(provider).lower()
    campaigns = live_list_campaigns(key)
    if not campaigns.get("ok"):
        return {**campaigns, "metrics": None, "items": []}
    if key == "meta":
        token = _secret("meta", "access_token", "META_ADS_ACCESS_TOKEN")
        account = meta_act_id()
        result = provider_request(
            "GET",
            f"https://graph.facebook.com/{graph_version()}/{account}/insights",
            query={"fields": "campaign_id,campaign_name,spend,impressions,clicks,reach,ctr,cpc,cpm,actions", "level": "campaign", "date_preset": "last_7d", "access_token": token},
        )
        data = result.get("json") if isinstance(result.get("json"), dict) else {}
        items = data.get("data") if isinstance(data.get("data"), list) else []
        return _from_http(key, result, items=items, metrics={"items": items, "unavailable": []})
    if key == "google":
        developer = _secret("google", "developer_token", "GOOGLE_ADS_DEVELOPER_TOKEN")
        token = _txt(refresh_google_access_token().get("access_token"))
        customer = _public("google", "customer_id", "GOOGLE_ADS_CUSTOMER_ID").replace("-", "")
        login = _public("google", "manager_id", "GOOGLE_ADS_LOGIN_CUSTOMER_ID").replace("-", "")
        headers = {"Authorization": f"Bearer {token}", "developer-token": developer, "Content-Type": "application/json"}
        if login:
            headers["login-customer-id"] = login
        result = provider_request(
            "POST",
            f"https://googleads.googleapis.com/{google_ads_version()}/customers/{customer}/googleAds:search",
            headers=headers,
            json_body={
                "query": "SELECT campaign.id, campaign.name, metrics.cost_micros, metrics.impressions, metrics.clicks, metrics.ctr, metrics.average_cpc, metrics.conversions FROM campaign WHERE segments.date DURING LAST_7_DAYS"
            },
        )
        data = result.get("json") if isinstance(result.get("json"), dict) else {}
        items = []
        for row in data.get("results") or []:
            camp = row.get("campaign") or {}
            metrics = row.get("metrics") or {}
            cost = metrics.get("costMicros") or metrics.get("cost_micros")
            items.append(
                {
                    "campaign_id": camp.get("id"),
                    "campaign_name": camp.get("name"),
                    "spend": int(cost) / 1_000_000 if cost else None,
                    "impressions": metrics.get("impressions"),
                    "clicks": metrics.get("clicks"),
                    "ctr": metrics.get("ctr"),
                    "cpc": (int(metrics.get("averageCpc") or metrics.get("average_cpc") or 0) / 1_000_000) or None,
                    "conversions": metrics.get("conversions"),
                }
            )
        return _from_http(key, result, items=items, metrics={"items": items})
    if key == "tiktok":
        token = _secret("tiktok", "access_token", "TIKTOK_ADS_ACCESS_TOKEN")
        advertiser = _public("tiktok", "advertiser_id", "TIKTOK_ADS_ADVERTISER_ID")
        result = provider_request(
            "GET",
            f"https://business-api.tiktok.com/open_api/{tiktok_version()}/report/integrated/get/",
            headers={"Access-Token": token},
            query={
                "advertiser_id": advertiser,
                "report_type": "BASIC",
                "data_level": "AUCTION_CAMPAIGN",
                "dimensions": json.dumps(["campaign_id"]),
                "metrics": json.dumps(["spend", "impressions", "clicks", "ctr", "cpc", "cpm", "conversion"]),
            },
        )
        data = result.get("json") if isinstance(result.get("json"), dict) else {}
        inner = data.get("data") if isinstance(data.get("data"), dict) else {}
        items = inner.get("list") if isinstance(inner.get("list"), list) else []
        return _from_http(key, result, items=items, metrics={"items": items})
    return adapter_result(ok=False, error="UNSUPPORTED", metrics=None, mode="LIVE")


def live_write_campaign(provider: str, action: str, *, campaign_id: str, budget: Any = None) -> dict[str, Any]:
    key = _txt(provider).lower()
    cid = _txt(campaign_id)
    if not cid:
        return adapter_result(ok=False, error="VALIDATION", message_ru="Нет campaign id.")
    if key == "meta":
        token = _secret("meta", "access_token", "META_ADS_ACCESS_TOKEN")
        fields: dict[str, Any] = {"access_token": token}
        if action == "pause":
            fields["status"] = "PAUSED"
        elif action == "resume":
            fields["status"] = "ACTIVE"
        elif action == "budget":
            fields["daily_budget"] = budget
        result = provider_request("POST", f"https://graph.facebook.com/{graph_version()}/{cid}", form={k: str(v) for k, v in fields.items() if v is not None})
        return _from_http(key, result, items=[{"id": cid}])
    if key == "google":
        return adapter_result(ok=False, error="UNSUPPORTED", message_ru="Google Ads mutate требует отдельного approve+mutate контракта.", mode="LIVE")
    if key == "tiktok":
        token = _secret("tiktok", "access_token", "TIKTOK_ADS_ACCESS_TOKEN")
        advertiser = _public("tiktok", "advertiser_id", "TIKTOK_ADS_ADVERTISER_ID")
        status = "DISABLE" if action == "pause" else "ENABLE"
        result = provider_request(
            "POST",
            f"https://business-api.tiktok.com/open_api/{tiktok_version()}/campaign/status/update/",
            headers={"Access-Token": token},
            json_body={"advertiser_id": advertiser, "campaign_ids": [cid], "operation_status": status},
        )
        return _from_http(key, result, items=[{"id": cid}])
    return adapter_result(ok=False, error="UNSUPPORTED", mode="LIVE")


def live_send_message(provider: str, *, to: str, text: str) -> dict[str, Any]:
    key = _txt(provider).lower()
    if key == "telegram":
        token = _secret("telegram", "bot_token", "VANGUARD_TELEGRAM_BOT_TOKEN")
        chat = _txt(to) or _public("telegram", "target_chat")
        if not token:
            return _not_configured(key)
        if not chat:
            return adapter_result(ok=False, error="VALIDATION", sent=False, message_ru="Не задан чат.")
        result = provider_request("POST", f"https://api.telegram.org/bot{token}/sendMessage", json_body={"chat_id": chat, "text": text})
        data = result.get("json") if isinstance(result.get("json"), dict) else {}
        ok = bool(result.get("ok") and data.get("ok"))
        inner = data.get("result") if isinstance(data.get("result"), dict) else {}
        packed = {**result, "ok": ok}
        out = _from_http(key, packed)
        out["sent"] = ok
        out["provider_message_id"] = inner.get("message_id")
        return out
    if key == "whatsapp":
        token = _secret("whatsapp", "access_token", "WHATSAPP_TOKEN")
        phone = _public("whatsapp", "phone_number_id", "WHATSAPP_PHONE_NUMBER_ID")
        if not token or not phone:
            return _not_configured(key)
        result = provider_request(
            "POST",
            f"https://graph.facebook.com/{graph_version()}/{phone}/messages",
            headers={"Authorization": f"Bearer {token}"},
            json_body={"messaging_product": "whatsapp", "to": to, "type": "text", "text": {"body": text}},
        )
        data = result.get("json") if isinstance(result.get("json"), dict) else {}
        messages = data.get("messages") if isinstance(data.get("messages"), list) else []
        out = _from_http(key, result)
        out["sent"] = bool(result.get("ok"))
        out["provider_message_id"] = (messages[0] or {}).get("id") if messages else None
        return out
    if key == "email":
        cfg = smtp_settings()
        if not cfg["host"] or not cfg["sender"] or not to:
            return _not_configured(key)
        msg = EmailMessage()
        msg["Subject"] = "Recruiting"
        msg["From"] = f"{cfg['sender_name']} <{cfg['sender']}>" if cfg["sender_name"] else cfg["sender"]
        msg["To"] = to
        msg.set_content(text)
        factory = _SMTP_FACTORY
        try:
            if factory:
                client = factory(cfg["host"], cfg["port"])
            elif cfg["tls_mode"] == "ssl":
                client = smtplib.SMTP_SSL(cfg["host"], cfg["port"], timeout=10)
            else:
                client = smtplib.SMTP(cfg["host"], cfg["port"], timeout=10)
            with client:
                client.ehlo()
                if cfg["tls_mode"] not in {"ssl", "none"}:
                    client.starttls(context=ssl.create_default_context())
                    client.ehlo()
                if cfg["user"]:
                    client.login(cfg["user"], cfg["password"] or "")
                client.send_message(msg)
            return adapter_result(
                ok=True,
                sent=True,
                status="CONNECTED",
                connected=True,
                mode="LIVE",
                provider="email",
                mocked_http=factory is not None,
                live_verified=factory is None,
                message_ru="Письмо отправлено.",
            )
        except Exception as exc:
            return adapter_result(ok=False, sent=False, error="PROVIDER_UNAVAILABLE", message_ru="SMTP отправка не удалась.", last_error=type(exc).__name__)
    return adapter_result(ok=False, error="UNSUPPORTED", sent=False)

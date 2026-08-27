"""Recruiting SMTP send path — SENT means accepted, never implied DELIVERED.

Uses existing services.observability metrics. Telegram is not used here.
"""

from __future__ import annotations

import hashlib
import re
import smtplib
import socket
import ssl
import time
from email.message import EmailMessage
from typing import Any

from services.observability import inc_metric, set_metric
from services.recruiting_ops.provider_contract import NOT_CONFIGURED, VALIDATION, adapter_result
from services.recruiting_ops.provider_errors import AUTH_ERROR, PROVIDER_UNAVAILABLE

TLS_ERROR = "TLS_ERROR"

MAX_EMAIL_ATTEMPTS = 3
EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}$")
HEADER_BAD = re.compile(r"[\r\n]")
SAFE_PLACEHOLDERS = ("name", "first_name", "vacancy", "company", "link")
TEMPLATES = {
    "intro": {
        "id": "intro",
        "label_ru": "Знакомство",
        "subject": "Вакансия {vacancy}",
        "body": "Здравствуйте, {name}. Рассмотрите вакансию {vacancy}.",
    },
    "interview": {
        "id": "interview",
        "label_ru": "Интервью",
        "subject": "Интервью: {vacancy}",
        "body": "Здравствуйте, {name}. Приглашаем на интервью по вакансии {vacancy}.",
    },
}


def _txt(value: Any) -> str:
    return str(value or "").strip()


def classify_smtp_exception(exc: BaseException) -> dict[str, Any]:
    name = type(exc).__name__
    text = str(exc).lower()
    code = getattr(exc, "smtp_code", None)
    if isinstance(exc, smtplib.SMTPRecipientsRefused) and not code:
        refused = exc.args[0] if exc.args else {}
        if isinstance(refused, dict) and refused:
            code = next(iter(refused.values()), (None, b""))[0]
    if code is not None:
        try:
            code = int(code)
        except (TypeError, ValueError):
            code = None
    if isinstance(exc, smtplib.SMTPAuthenticationError) or name == "SMTPAuthenticationError" or "authentication" in text:
        return {"error": AUTH_ERROR, "status": "ERROR", "retryable": False, "message_ru": "Ошибка авторизации SMTP."}
    if isinstance(exc, (TimeoutError, socket.timeout, smtplib.SMTPServerDisconnected)) or "timed out" in text or name in {"TimeoutError", "timeout"}:
        return {"error": PROVIDER_UNAVAILABLE, "status": "ERROR", "retryable": True, "message_ru": "Таймаут SMTP."}
    if isinstance(exc, (ssl.SSLError, smtplib.SMTPNotSupportedError)) or "ssl" in text or "tls" in text or name in {"SSLError", "SSLEOFError"}:
        return {"error": TLS_ERROR, "status": "ERROR", "retryable": False, "message_ru": "Ошибка TLS/SSL SMTP."}
    if code in {421, 450, 451, 452}:
        return {"error": PROVIDER_UNAVAILABLE, "status": "ERROR", "retryable": True, "message_ru": "Временная ошибка SMTP."}
    if code and code >= 500:
        return {"error": PROVIDER_UNAVAILABLE, "status": "ERROR", "retryable": False, "message_ru": "Постоянная ошибка SMTP."}
    return {"error": PROVIDER_UNAVAILABLE, "status": "ERROR", "retryable": True, "message_ru": "SMTP недоступен."}


def valid_recipient(address: str) -> bool:
    return bool(EMAIL_RE.match(_txt(address)))


def header_injection(value: str) -> bool:
    return bool(HEADER_BAD.search(value or ""))


def render_template(template_id: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
    spec = TEMPLATES.get(_txt(template_id) or "intro") or TEMPLATES["intro"]
    ctx = {key: _txt((context or {}).get(key)) for key in SAFE_PLACEHOLDERS}

    def _safe(match: re.Match[str]) -> str:
        key = match.group(1)
        if key not in SAFE_PLACEHOLDERS:
            return ""
        return ctx.get(key) or ""

    subject = re.sub(r"\{([A-Za-z0-9_]+)\}", _safe, spec["subject"])
    body = re.sub(r"\{([A-Za-z0-9_]+)\}", _safe, spec["body"])
    return {"ok": True, "template_id": spec["id"], "subject": subject, "body": body, "label_ru": spec["label_ru"]}


def idempotency_key(*, organization_id: str, to: str, subject: str, body: str, candidate_id: str = "") -> str:
    raw = "|".join([organization_id, to.lower(), subject, body, candidate_id])
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def record_health_metric(status: str, latency_ms: int | None = None) -> None:
    if status == "CONNECTED":
        set_metric("email_provider_health", 1)
    elif status == "NOT_CONFIGURED":
        set_metric("email_provider_health", 0)
    else:
        set_metric("email_provider_health", -1)
    if latency_ms is not None:
        set_metric("email_send_latency", float(latency_ms))


def send_smtp_message(
    *,
    to: str,
    subject: str,
    body: str,
    cfg: dict[str, Any],
    factory: Any = None,
) -> dict[str, Any]:
    if not cfg.get("host") or not cfg.get("sender"):
        record_health_metric("NOT_CONFIGURED")
        return adapter_result(ok=False, error=NOT_CONFIGURED, status="NOT_CONFIGURED", sent=False, delivered=False, message_ru="SMTP не настроен.")
    if not valid_recipient(to):
        return adapter_result(ok=False, error=VALIDATION, status="ERROR", sent=False, delivered=False, message_ru="Некорректный получатель.")
    if header_injection(to) or header_injection(subject) or header_injection(cfg.get("sender") or ""):
        return adapter_result(ok=False, error=VALIDATION, status="ERROR", sent=False, delivered=False, message_ru="Обнаружена инъекция заголовка.")
    msg = EmailMessage()
    msg["Subject"] = subject
    sender_name = _txt(cfg.get("sender_name"))
    msg["From"] = f"{sender_name} <{cfg['sender']}>" if sender_name else cfg["sender"]
    msg["To"] = to
    msg.set_content(body)
    last_error: dict[str, Any] = {}
    started = time.perf_counter()
    inc_metric("email_send_attempt_total")
    for attempt in range(1, MAX_EMAIL_ATTEMPTS + 1):
        try:
            if factory:
                client = factory(cfg["host"], cfg["port"])
            elif str(cfg.get("tls_mode") or "").lower() == "ssl":
                client = smtplib.SMTP_SSL(cfg["host"], int(cfg["port"]), timeout=10)
            else:
                client = smtplib.SMTP(cfg["host"], int(cfg["port"]), timeout=10)
            with client:
                client.ehlo()
                if str(cfg.get("tls_mode") or "starttls").lower() not in {"ssl", "none"}:
                    client.starttls(context=ssl.create_default_context())
                    client.ehlo()
                if cfg.get("user"):
                    client.login(cfg.get("user") or "", cfg.get("password") or "")
                client.send_message(msg)
            latency = int((time.perf_counter() - started) * 1000)
            inc_metric("email_send_success_total")
            record_health_metric("CONNECTED", latency)
            return adapter_result(
                ok=True,
                sent=True,
                delivered=False,
                delivery="accepted",
                status="SENT",
                connected=True,
                mode="LIVE",
                provider="email",
                mocked_http=factory is not None,
                live_verified=factory is None,
                latency_ms=latency,
                attempt=attempt,
                message_ru="SMTP принял письмо. Доставка не подтверждена.",
            )
        except Exception as exc:
            last_error = classify_smtp_exception(exc)
            if last_error.get("retryable") and attempt < MAX_EMAIL_ATTEMPTS:
                inc_metric("email_retry_total")
                continue
            break
    latency = int((time.perf_counter() - started) * 1000)
    inc_metric("email_send_failure_total")
    record_health_metric(str(last_error.get("status") or "ERROR"), latency)
    return adapter_result(
        ok=False,
        sent=False,
        delivered=False,
        status="FAILED",
        error=last_error.get("error"),
        retryable=bool(last_error.get("retryable")),
        mode="LIVE",
        provider="email",
        latency_ms=latency,
        message_ru=last_error.get("message_ru"),
        last_error=last_error.get("error"),
    )

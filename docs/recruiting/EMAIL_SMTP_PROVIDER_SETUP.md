# Recruiting Email SMTP provider setup

No real credentials belong in this file, git, the frontend, API payloads, logs, or audit records.

Email is the production messaging channel for Recruiting in sprint `recruiting_1.10`. Telegram is intentionally frozen/disabled and does not block core readiness.

## Required environment variables

| Name | Secret | Purpose |
| --- | --- | --- |
| `SMTP_HOST` | no | SMTP hostname |
| `SMTP_PORT` | no | Port (default `587`) |
| `SMTP_USER` | no | SMTP username |
| `SMTP_PASSWORD` | **yes** | SMTP password |
| `SMTP_TLS_MODE` | no | `starttls` (default), `ssl`, or `none` |
| `EMAIL_FROM` | no | Envelope / From address |
| `EMAIL_FROM_NAME` | no | Optional display name |
| `EMAIL_SEND_RATE_LIMIT` | no | Sends per org per window (default `20`) |

Wizard-submitted secrets go to SecretStore (`email.smtp_password`). `describe()` returns presence only (`value: null`).

Missing host or sender ⇒ **NOT_CONFIGURED**. That is valid. Do not invent CONNECTED.

## TLS / SSL

- Default: STARTTLS on port 587 (`SMTP_TLS_MODE=starttls`).
- Implicit TLS: `SMTP_TLS_MODE=ssl` (typically port 465).
- `none` is for isolated lab relays only — not a production default.
- TLS/SSL handshake failure ⇒ status **ERROR**, error `TLS_ERROR`. Not retried.
- Authentication failure ⇒ **ERROR**, `AUTH_ERROR`. Not retried.

## Provider state meanings

| Status | Meaning |
| --- | --- |
| `NOT_CONFIGURED` | Host or From missing. Core Recruiting still healthy. |
| `CONFIGURING` | Credentials saved; live health not verified. |
| `CONNECTED` | EHLO/login succeeded. **No email is sent during health check.** |
| `ERROR` | Auth, timeout, TLS, or provider failure. |
| Telegram `DISABLED` | Intentionally frozen. Not an Email state. |

`MOCK` is never reported as LIVE. Injected SMTP in tests is `mocked_http=true`, `live_verified=false`.

## Render setup

1. In the Render dashboard, set the env names above on the API service. Do not paste values into git.
2. Public origin (from `VANGUARD_WEBSITE_URL`): `https://ados-web.onrender.com`.
3. Restart the service after rotation.
4. Open **Recruiting → Интеграции → Email → Проверить соединение**.
5. CONNECTED only after a real SMTP handshake.

## Health check

`POST /api/recruiting-ops/v1/providers/email/test-connection`

- Connects, EHLO, optional STARTTLS/SSL, optional LOGIN.
- Does **not** send mail.
- Metrics: `email_provider_health` (1 connected, 0 not configured, -1 error), `email_send_latency`.

## Test email

Requires an explicit owner/recruiter action.

`POST /api/recruiting-ops/v1/providers/email/test-email` with `{ "to": "..." }`

Health check never triggers this path. Observer is forbidden.

## Candidate email

UI: **Кандидаты → Письмо**.

- Templates: `intro`, `interview`. Placeholders limited to `{name, first_name, vacancy, company, link}`. Unknown placeholders render empty.
- Preview: `POST /email/preview`.
- Send: `POST /candidates/{id}/email`.
- History: `GET /candidates/{id}/emails`.
- Persists `communication` + candidate timeline activity.

## Campaign approval

Campaign blast (`campaign_id` without `approved`) returns `APPROVAL_REQUIRED`. Direct 1:1 owner send does not skip SMTP health; it still requires a connected SMTP path. Live campaign writes remain `ACTION_PENDING_APPROVAL`.

## Retry

Bounded to 3 attempts (`MAX_EMAIL_ATTEMPTS`).

- Temporary (timeout, 421/450/451/452): retried.
- Permanent (5xx, auth, TLS): not retried.
- Metric: `email_retry_total`.

## Rate limiting

Reuses `services/recruiting_ops/public_limits.check_rate_limit` (no second stack).

Key: `email-send:{organization_id}`. Exceeded ⇒ `RATE_LIMITED` and `email_rate_limited_total`.

## Dedup

SHA-256 idempotency key over org, recipient, subject, body, candidate id. A successful SENT communication is not sent twice.

## Suppression

`POST /email/suppression` `{ "email": "..." }`. Matching recipient is not sent (`error=suppressed`).

## Security

- Password never returned by API, UI, logs, or audit (presence boolean only).
- Header CR/LF injection in From/To/Subject is rejected.
- Invalid recipients are rejected.
- Observer cannot test-connect or send.
- SENT means SMTP **accepted**. It is **never** auto-marked `DELIVERED`.

## Secret rotation

1. Put a new `SMTP_PASSWORD` in Render / SecretStore (`rotate`).
2. Do not commit values.
3. **Проверить соединение**.
4. Old password is not shown; previous envelope is replaced.

## Troubleshooting

| Symptom | Check |
| --- | --- |
| NOT_CONFIGURED | `SMTP_HOST` and `EMAIL_FROM` |
| AUTH_ERROR | User/password; some providers need an app password |
| TLS_ERROR | Port vs `SMTP_TLS_MODE` (587/starttls vs 465/ssl) |
| Timeout | Network egress from Render to the SMTP host |
| RATE_LIMITED | Wait for the window or raise `EMAIL_SEND_RATE_LIMIT` |
| APPROVAL_REQUIRED | Approve the campaign write / pass `approved` after human approval |
| suppressed | Remove the address from suppression if send is intended |
| Telegram card frozen | Expected. It does not block Email or core health. |

## Observability

Existing `services/observability.py` metrics (Prometheus text):

- `email_send_attempt_total`
- `email_send_success_total`
- `email_send_failure_total`
- `email_retry_total`
- `email_rate_limited_total`
- `email_provider_health`
- `email_send_latency`

Do not add a second monitoring stack.

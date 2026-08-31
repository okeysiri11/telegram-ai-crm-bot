# Recruiting WhatsApp Cloud API provider setup

No real credentials belong in this file, git, the frontend, API payloads, logs, audit records, or Cursor chat.

WhatsApp is the production messaging channel for Recruiting in sprint `recruiting_1.12`. Telegram remains intentionally frozen/disabled and does not block core readiness. Meta Ads / Google Ads / TikTok Ads are not connected in this sprint.

## Required values from Meta

Obtain these from Meta Business / WhatsApp Cloud API (App Dashboard → WhatsApp → API Setup, and Webhooks):

| Name | Secret | Purpose |
| --- | --- | --- |
| `WHATSAPP_ACCESS_TOKEN` | **yes** | Cloud API access token. Canonical name. |
| `WHATSAPP_TOKEN` | **yes** | Backwards-compatible alias for `WHATSAPP_ACCESS_TOKEN` only |
| `WHATSAPP_PHONE_NUMBER_ID` | no | Phone number identifier used in Graph URLs |
| `WHATSAPP_BUSINESS_ACCOUNT_ID` | no | WABA id (needed to list message templates) |
| `WHATSAPP_VERIFY_TOKEN` | **yes** | Token you choose; Meta must send the same value on webhook GET verify |
| `WHATSAPP_APP_SECRET` | **yes** | App secret for `X-Hub-Signature-256` on webhook POST |

Optional: `WHATSAPP_SEND_RATE_LIMIT` (default `20` per org window).

Do **not** paste access tokens into Cursor chat. Enter them in Render / the server secret store, or in **Recruiting → Интеграции → WhatsApp → Настроить**.

## Webhook URL (production)

From deployed configuration (`VANGUARD_WEBSITE_URL` / `RECRUITING_PUBLIC_URL`):

`https://ados-web.onrender.com/api/recruiting-ops/v1/webhooks/whatsapp`

Subscribe Meta webhooks to this URL.

- GET: hub challenge verify (`hub.mode=subscribe`, `hub.verify_token`, `hub.challenge`)
- POST: inbound messages and status callbacks (`sent` / `delivered` / `read` / `failed`)

Local: `http://127.0.0.1:8080/api/recruiting-ops/v1/webhooks/whatsapp`

## Where to enter values

1. **Server / Render env** — set the names above on the API service. Restart after rotation.
2. **Recruiting UI** — **Recruiting → Интеграции → WhatsApp → Настроить**:
   - Phone identifier → `WHATSAPP_PHONE_NUMBER_ID`
   - API token → `WHATSAPP_ACCESS_TOKEN`
   - Webhook verify token → `WHATSAPP_VERIFY_TOKEN`
   - App Secret → `WHATSAPP_APP_SECRET`
   - Business account → `WHATSAPP_BUSINESS_ACCOUNT_ID`
3. Click **Проверить соединение**. Health is Graph `GET /{phone_number_id}` only. **It never sends a WhatsApp message.**

Missing token or phone id ⇒ **NOT_CONFIGURED**. That is valid. Do not invent CONNECTED.

`GET /api/recruiting-ops/v1/health` → `whatsapp.env_status` (no secret values):

| Status | Meaning |
| --- | --- |
| `NOT_CONFIGURED` | None of the required env/store fields are present |
| `PARTIALLY_CONFIGURED` | Some required fields present, not all |
| `READY_FOR_LIVE_CHECK` | Token, phone number id, verify token, and app secret are present. Graph has **not** been called |

Required for `READY_FOR_LIVE_CHECK`: `WHATSAPP_ACCESS_TOKEN` (or alias `WHATSAPP_TOKEN`), `WHATSAPP_PHONE_NUMBER_ID`, `WHATSAPP_VERIFY_TOKEN`, `WHATSAPP_APP_SECRET`. `WHATSAPP_BUSINESS_ACCOUNT_ID` is optional (needed to list templates).

## Provider state meanings

| Status | Meaning |
| --- | --- |
| `NOT_CONFIGURED` | Access token missing. Core Recruiting still healthy. |
| `CONFIGURING` | Credentials saved; live health not verified. Saving does **not** auto-connect. |
| `CONNECTED` | Authenticated Graph health succeeded. No message was sent. |
| `ERROR` | Auth or provider failure. |
| Telegram `DISABLED` | Intentionally frozen. Not a WhatsApp state. |

`MOCK` is never reported as LIVE/CONNECTED in production. Injected HTTP in tests is `mocked_http=true`, `live_verified=false` — not production evidence.

## Send, inbound, statuses, templates

- Outbound: `POST /candidates/{id}/whatsapp`. Real send requires `confirm=true` (human). Provider HTTP 200 means **accepted**, not delivered.
- Conversations: `GET /whatsapp/conversations?candidate_id=`
- Inbound POST webhook persists incoming messages. Candidate match is by normalized phone. Unmatched senders are `unresolved`.
- Status webhooks update sent / delivered / read / failed. Failed webhooks are not retried forever.
- Templates: `GET /whatsapp/templates` lists WABA templates. Outbound template send uses the same Cloud API `/{phone_number_id}/messages` path with `type: template` (name + language + optional components/parameters). No production template name is hard-coded.
- 24-hour window: session text is allowed only after a customer inbound within 24 hours. First outbound or expired window returns `TEMPLATE_REQUIRED` (`TEMPLATE_REQUIRED_NO_INBOUND` / `TEMPLATE_REQUIRED_WINDOW_EXPIRED`) and does **not** send a text message.
- Idempotency: `Idempotency-Key` header or `idempotency_key` body. The same key does not create a second Meta send after `SENT`. A previous `FAILED` send with the same key may retry deterministically.
- `phone_number_id` → organization is persisted (`whatsapp_phone_map`) and reloaded after restart. Unknown ids are rejected (`UNKNOWN_PHONE_NUMBER_ID`).

UI actions: Написать, Ответить, Создать с AI, Отправить. AI draft never sends. **Отправить** still requires a second human confirmation.

## Retry and rate limit

Uses existing `provider_http` (max 4 attempts) and `public_limits.check_rate_limit`. Key: `whatsapp-send:{organization_id}`. 429 / 5xx may retry; 4xx auth is permanent. Respects `Retry-After` when present. No retry storms.

## Security

- Tokens never returned by API, UI, logs, audit, or metrics labels.
- Webhook POST verifies `X-Hub-Signature-256` when app secret is set.
- Duplicate webhook ids are ignored (`whatsapp_webhook_duplicate_total`).
- Organization / workspace isolation: conversations and credentials are org-scoped.
- Observer cannot configure or send.

## Observability

Existing `services/observability.py` (no second stack):

- `whatsapp_send_attempt_total`
- `whatsapp_send_success_total`
- `whatsapp_send_failure_total`
- `whatsapp_webhook_received_total`
- `whatsapp_webhook_duplicate_total`
- `whatsapp_message_delivered_total`
- `whatsapp_message_read_total`
- `whatsapp_provider_health`
- `whatsapp_rate_limited_total`
- `whatsapp_send_latency`

Labels never include phones, message text, tokens, names, or emails.

## Troubleshooting

| Symptom | Check |
| --- | --- |
| NOT_CONFIGURED | `WHATSAPP_ACCESS_TOKEN` / `WHATSAPP_TOKEN` and `WHATSAPP_PHONE_NUMBER_ID` |
| AUTH_ERROR | Token expired or missing WhatsApp permission |
| INVALID_ACCOUNT | Phone number id |
| Webhook verify failed | `WHATSAPP_VERIFY_TOKEN` matches Meta |
| Signature rejected | `WHATSAPP_APP_SECRET` / App Secret |
| RATE_LIMITED | Wait or raise `WHATSAPP_SEND_RATE_LIMIT` |
| Accepted but not delivered | Wait for Meta `delivered` webhook — SENT ≠ DELIVERED |
| Telegram card frozen | Expected. Does not block WhatsApp. |

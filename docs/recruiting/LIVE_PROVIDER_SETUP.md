# Recruiting live provider setup

No secret values. Configure these in the server environment or Render dashboard, then **Recruiting → Интеграции → Проверить соединение**.

Public API origin used for callbacks:

- Production (from `VANGUARD_WEBSITE_URL` host): `https://ados-web.onrender.com`
- Override: `RECRUITING_PUBLIC_URL`
- Local: `http://127.0.0.1:8080`

Callback pattern: `{origin}/api/recruiting-ops/v1/oauth/{provider}/callback`

Successful live status is **Подключено / CONNECTED** only after a real provider health request. Missing credentials stay **Не настроено / NOT_CONFIGURED** (not ERROR).

---

## Meta Ads

1. Meta for Developers app with Marketing API.
2. Create app; add Ads Management; set Valid OAuth Redirect URIs.
3. Env names: `META_ADS_APP_ID`, `META_ADS_APP_SECRET`, `META_ADS_ACCOUNT_ID`, optional `META_ADS_ACCESS_TOKEN`, `META_ADS_REDIRECT_URI`, `META_GRAPH_API_VERSION`.
4. Redirect URI: `https://ados-web.onrender.com/api/recruiting-ops/v1/oauth/meta/callback` (or local `http://127.0.0.1:8080/api/recruiting-ops/v1/oauth/meta/callback`).
5. Scopes: `ads_management`, `ads_read`, `business_management`, `pages_show_list`.
6. Enter App ID / secret and Ad Account ID in Recruiting → Интеграции → Meta Ads → Настроить, or set env. Then **Подключить**.
7. **Проверить соединение**.
8. Success: status **Подключено**, mode **LIVE**.

---

## Google Ads

1. Google Cloud OAuth client + Google Ads API developer token.
2. Create OAuth client (web), enable Google Ads API, note customer ID (and manager ID if MCC).
3. Env names: `GOOGLE_ADS_CLIENT_ID`, `GOOGLE_ADS_CLIENT_SECRET`, `GOOGLE_ADS_DEVELOPER_TOKEN`, `GOOGLE_ADS_CUSTOMER_ID`, optional `GOOGLE_ADS_REFRESH_TOKEN`, `GOOGLE_ADS_LOGIN_CUSTOMER_ID`, `GOOGLE_ADS_REDIRECT_URI`, `GOOGLE_ADS_API_VERSION`.
4. Redirect URI: `https://ados-web.onrender.com/api/recruiting-ops/v1/oauth/google/callback`.
5. Scope: `https://www.googleapis.com/auth/adwords` (offline access).
6. Recruiting → Интеграции → Google Ads → Настроить / **Подключить**.
7. **Проверить соединение**.
8. Success: **Подключено**.

---

## TikTok Ads

1. TikTok Marketing API app.
2. Create app; add redirect URL; note advertiser ID.
3. Env names: `TIKTOK_ADS_APP_ID`, `TIKTOK_ADS_APP_SECRET`, `TIKTOK_ADS_ADVERTISER_ID`, optional `TIKTOK_ADS_ACCESS_TOKEN`, `TIKTOK_ADS_REDIRECT_URI`.
4. Redirect URI: `https://ados-web.onrender.com/api/recruiting-ops/v1/oauth/tiktok/callback`.
5. Advertiser management authorization.
6. Recruiting → Интеграции → TikTok Ads → Настроить / **Подключить**.
7. **Проверить соединение**.
8. Success: **Подключено**.

---

## Telegram

Telegram is **intentionally frozen / disabled** in Recruiting.

- Status: `DISABLED` (Отключено / заморожено).
- No «Подключить» CTA.
- Frozen overlay does not change core Recruiting readiness.
- Tracking destinations stay `WAITING_PROVIDER` — no retry storm.
- Do not reuse platform `BOT_TOKEN`. Adapter HTTP is unchanged and is not developed in this sprint.

---

## WhatsApp

1. Meta WhatsApp Cloud API (WhatsApp product on a Meta app + business phone number).
2. From Meta obtain: `WHATSAPP_ACCESS_TOKEN`, `WHATSAPP_PHONE_NUMBER_ID`, `WHATSAPP_BUSINESS_ACCOUNT_ID`, `WHATSAPP_VERIFY_TOKEN`. Optional `WHATSAPP_APP_SECRET` for webhook signatures. `WHATSAPP_TOKEN` is an accepted alias for the access token.
3. Enter values in **Recruiting → Интеграции → WhatsApp → Настроить**, or as Render/server env. Do not paste tokens into chat or git.
4. Webhook URL (production): `https://ados-web.onrender.com/api/recruiting-ops/v1/webhooks/whatsapp`
5. Local webhook: `http://127.0.0.1:8080/api/recruiting-ops/v1/webhooks/whatsapp`
6. **Проверить соединение** — Graph health only, no outbound message.
7. Success: **Подключено / CONNECTED** only after a real authenticated Meta response. Missing credentials stay **Не настроено / NOT_CONFIGURED**.
8. Outbound send always requires a human confirmation. AI draft does not send. Provider accept ≠ delivered.
9. Full owner steps: `docs/recruiting/WHATSAPP_PROVIDER_SETUP.md`.

---

## Email (SMTP)

1. SMTP mailbox (SendGrid/Mailgun/SES API can be added later without redesign).
2. Host, port, TLS mode, user, password, sender.
3. Env names: `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_TLS_MODE`, `EMAIL_FROM`, `EMAIL_FROM_NAME`.
4. No OAuth redirect.
5. STARTTLS by default (`SMTP_TLS_MODE=starttls`).
6. Recruiting → Интеграции → Email → Настроить. Password is not shown after save.
7. **Проверить соединение**.
8. Success: **Подключено**. Outbound recruiting messages still require human approval.

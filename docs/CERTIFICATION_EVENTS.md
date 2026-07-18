# Event System Certification

> Generated: 2026-07-18 13:53:32 UTC

## Verdict: **FAIL**

## Canonical Bus

- **PlatformEventBus** (`events/event_bus.py`) — canonical in-process bus
- **events/publisher.py** — unified publish entry

## Adapters

- CRM Outbox (`services/crm_event_bus.py`) — persists after `publish_crm_to_platform_bus`
- Legacy EventBus — re-exported via `platform_legacy` in `events/__init__.py`

- CRM adapter wired to PlatformEventBus: **unknown**
- Direct legacy publishers in pg engines: **15**

## Direct CRM Publishers (must migrate to events/publisher)

- `services/pg_deal_workflow.py`
- `services/pg_pricing_engine.py`
- `services/pg_partner_engine.py`
- `services/pg_market_data_engine.py`
- `services/pg_automotive_cost_engine.py`
- `services/pg_automotive_operations_engine.py`
- `services/pg_kyc_aml_engine.py`
- `services/pg_client_request_crm_engine.py`
- `services/pg_otc_matching_engine.py`
- `services/pg_observability_engine.py`
- `services/pg_settlement_engine.py`
- `services/pg_liquidity_engine.py`
- `services/pg_risk_engine.py`
- `services/pg_automotive_marketplace_engine.py`
- `services/pg_webhook_engine.py`

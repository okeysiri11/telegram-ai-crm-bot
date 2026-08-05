# Tenant Isolation Audit — Sprint 30.0

Scanned `repositories/*.py`. Heuristic findings (not confirmed leaks):

**Count:** 79

| File | Function | Line | Issue |
|---|---|---|---|
| `repositories/ai_advertising_agent_repository.py` | `get_by_id` | 72 | query_without_tenant_mention |
| `repositories/ai_advertising_agent_repository.py` | `list_active` | 96 | query_without_tenant_mention |
| `repositories/ai_advertising_agent_repository.py` | `list_by_campaign` | 176 | query_without_tenant_mention |
| `repositories/ai_conversation_skills_repository.py` | `update_fields` | 219 | query_without_tenant_mention |
| `repositories/ai_sales_agent_repository.py` | `get_by_id` | 87 | query_without_tenant_mention |
| `repositories/ai_sales_agent_repository.py` | `list_by_lead` | 207 | query_without_tenant_mention |
| `repositories/ai_sales_agent_repository.py` | `get_by_id` | 268 | query_without_tenant_mention |
| `repositories/ai_sales_agent_repository.py` | `list_by_lead` | 274 | query_without_tenant_mention |
| `repositories/ai_sales_agent_repository.py` | `get_by_lead` | 370 | query_without_tenant_mention |
| `repositories/audit_repository.py` | `list_by_entity` | 55 | query_without_tenant_mention |
| `repositories/audit_repository.py` | `list_by_user` | 73 | query_without_tenant_mention |
| `repositories/audit_repository.py` | `list_by_company` | 96 | query_without_tenant_mention |
| `repositories/audit_repository.py` | `list_recent` | 110 | query_without_tenant_mention |
| `repositories/automotive_partner_repository.py` | `get_partner_by_id` | 24 | query_without_tenant_mention |
| `repositories/automotive_partner_repository.py` | `get_partner_by_code` | 30 | query_without_tenant_mention |
| `repositories/automotive_partner_repository.py` | `list_partners` | 39 | query_without_tenant_mention |
| `repositories/automotive_partner_repository.py` | `list_products_for_partner` | 53 | query_without_tenant_mention |
| `repositories/automotive_partner_repository.py` | `get_product_by_code` | 69 | query_without_tenant_mention |
| `repositories/automotive_partner_repository.py` | `get_branding` | 146 | query_without_tenant_mention |
| `repositories/automotive_partner_repository.py` | `list_ctas` | 155 | query_without_tenant_mention |
| `repositories/car_repository.py` | `get_car` | 175 | query_without_tenant_mention |
| `repositories/channel_integration_repository.py` | `get_by_id` | 60 | query_without_tenant_mention |
| `repositories/commercial_billing_repository.py` | `get_by_id` | 65 | query_without_tenant_mention |
| `repositories/commercial_billing_repository.py` | `list_pending` | 71 | query_without_tenant_mention |
| `repositories/commercial_billing_repository.py` | `list_by_user` | 80 | query_without_tenant_mention |
| `repositories/commercial_billing_repository.py` | `get_by_payment` | 140 | query_without_tenant_mention |
| `repositories/communication_hub_repository.py` | `get_by_id` | 65 | query_without_tenant_mention |
| `repositories/communication_hub_repository.py` | `update_fields` | 181 | query_without_tenant_mention |
| `repositories/communication_hub_repository.py` | `get_by_id` | 255 | query_without_tenant_mention |
| `repositories/cross_posting_repository.py` | `get_by_id` | 60 | query_without_tenant_mention |
| `repositories/cross_posting_repository.py` | `get_by_id` | 186 | query_without_tenant_mention |
| `repositories/cross_posting_repository.py` | `list_due` | 213 | query_without_tenant_mention |
| `repositories/cross_posting_repository.py` | `get_by_job` | 317 | query_without_tenant_mention |
| `repositories/cross_posting_repository.py` | `update_fields` | 337 | query_without_tenant_mention |
| `repositories/deal_pipeline_repository.py` | `get_by_id` | 116 | query_without_tenant_mention |
| `repositories/deal_pipeline_repository.py` | `list_by_deal` | 283 | query_without_tenant_mention |
| `repositories/deal_pipeline_repository.py` | `list_by_deal` | 333 | query_without_tenant_mention |
| `repositories/deal_pipeline_repository.py` | `update_fields` | 362 | query_without_tenant_mention |
| `repositories/deal_pipeline_repository.py` | `list_by_deal` | 408 | query_without_tenant_mention |
| `repositories/dealer_portal_repository.py` | `dismiss` | 112 | query_without_tenant_mention |
| `repositories/lead_automation_repository.py` | `get_by_id` | 96 | query_without_tenant_mention |
| `repositories/lead_automation_repository.py` | `find_duplicate` | 102 | query_without_tenant_mention |
| `repositories/lead_automation_repository.py` | `count_open_leads` | 196 | query_without_tenant_mention |
| `repositories/lead_automation_repository.py` | `list_source_events` | 229 | query_without_tenant_mention |
| `repositories/lead_automation_repository.py` | `source_stats` | 243 | query_without_tenant_mention |
| `repositories/lead_marketplace_repository.py` | `get_by_id` | 78 | query_without_tenant_mention |
| `repositories/lead_marketplace_repository.py` | `list_open` | 105 | query_without_tenant_mention |
| `repositories/lead_marketplace_repository.py` | `get_by_id` | 181 | query_without_tenant_mention |
| `repositories/lead_marketplace_repository.py` | `list_by_listing` | 187 | query_without_tenant_mention |
| `repositories/lead_marketplace_repository.py` | `get_highest_bid` | 208 | query_without_tenant_mention |
| `repositories/lead_marketplace_repository.py` | `mark_outbid` | 224 | query_without_tenant_mention |
| `repositories/lead_marketplace_repository.py` | `count_by_listing` | 239 | query_without_tenant_mention |
| `repositories/partner_tenant_repository.py` | `get_by_code` | 59 | query_without_tenant_mention |
| `repositories/partner_tenant_repository.py` | `list_by_company` | 72 | query_without_tenant_mention |
| `repositories/partner_tenant_repository.py` | `list_active` | 90 | query_without_tenant_mention |
| `repositories/partner_tenant_repository.py` | `list_by_user` | 162 | query_without_tenant_mention |
| `repositories/recommendation_engine_repository.py` | `get_by_id` | 73 | query_without_tenant_mention |
| `repositories/recommendation_engine_repository.py` | `get_by_id` | 172 | query_without_tenant_mention |
| `repositories/recommendation_engine_repository.py` | `list_by_profile` | 178 | query_without_tenant_mention |
| `repositories/recommendation_engine_repository.py` | `list_by_profile` | 233 | query_without_tenant_mention |
| `repositories/revenue_sharing_repository.py` | `get_by_id` | 60 | query_without_tenant_mention |
| `repositories/revenue_sharing_repository.py` | `list_active` | 97 | query_without_tenant_mention |
| `repositories/revenue_sharing_repository.py` | `upsert` | 111 | query_without_tenant_mention |
| `repositories/revenue_sharing_repository.py` | `get_by_id` | 148 | query_without_tenant_mention |
| `repositories/revenue_sharing_repository.py` | `upsert` | 161 | query_without_tenant_mention |
| `repositories/revenue_sharing_repository.py` | `list_by_agreement` | 195 | query_without_tenant_mention |
| `repositories/revenue_sharing_repository.py` | `get_by_id` | 209 | query_without_tenant_mention |
| `repositories/revenue_sharing_repository.py` | `list_by_agreement` | 246 | query_without_tenant_mention |
| `repositories/revenue_sharing_repository.py` | `get_by_id` | 260 | query_without_tenant_mention |
| `repositories/tenant_billing_repository.py` | `list_active` | 77 | query_without_tenant_mention |
| `repositories/tenant_billing_repository.py` | `get_by_id` | 256 | query_without_tenant_mention |
| `repositories/tenant_billing_repository.py` | `get_by_number` | 262 | query_without_tenant_mention |
| `repositories/tenant_billing_repository.py` | `count_for_period_prefix` | 282 | query_without_tenant_mention |
| `repositories/tenant_billing_repository.py` | `list_by_invoice` | 319 | query_without_tenant_mention |
| `repositories/tenant_foundation_repository.py` | `get_by_code` | 22 | query_without_tenant_mention |
| `repositories/tenant_foundation_repository.py` | `list_active` | 54 | query_without_tenant_mention |
| `repositories/trust_security_repository.py` | `get_by_id` | 271 | query_without_tenant_mention |
| `repositories/trust_security_repository.py` | `get_by_id` | 342 | query_without_tenant_mention |
| `repositories/trust_security_repository.py` | `list_active` | 365 | query_without_tenant_mention |

## Remediation

- Prefer `repositories.tenant_scope.apply_tenant_filter(..., required=True)`.
- Cross-tenant admin tools must pass `required=False` explicitly and log the bypass.
- See `docs/TENANT_ISOLATION.md`.

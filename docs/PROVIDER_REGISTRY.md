# Provider Registry

**Sprint:** 31.2  
**Web:** `src/web/src/enterprise-integrations/providerRegistry.ts`  
**Python:** `platform_integrations/extended_provider_catalog.py`  
**AI kinds:** `platform_enterprise_ai_provider_hub/models.py`

## Categories

AI · Image · Video · Audio · Automation · CRM · Storage · Payments · Observability · Orchestration

## Meta

| Concern | Owner |
|---|---|
| Credential vault | Enterprise Secrets Hub (ESH) |
| AI gateway | APH |
| External orchestrator | n8n (bridge only) |
| System of record | Platform Runtime |
| Prompt firewall | APH / `prompt_firewall` |
| Rate limits | `platform_integrations.rate_limiter` |
| Audit | n8n_bridge audit + platform observability |

## Image / Video / Audio (catalog)

Declared for Production Studio selector; connectors deepen behind APH without a second registry.

## CRM / Storage / Payments / Observability

Declared for Integration Hub wizards; reuse existing finance / CRM / obs prefixes — no parallel SDKs.

## Related

`AI_PROVIDERS.md`, `INTEGRATION_HUB.md`, `knowledge/providers/PROVIDER_REGISTRY.md`

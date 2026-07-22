# Auto AI — Vehicle Intelligence (Sprint 10.3)

AI recommendations, pricing, inspection, forecasting, and buyer assistant for **Auto Marketplace 1.6.0-alpha**.

| Field | Value |
|-------|-------|
| Application version | `1.6.0-alpha` |
| Auto AI engine | `1.0` |
| Recommendation engine | `1.0` |
| API | `/api/auto/v1/ai` · `/recommendations` · `/pricing-ai` · `/inspection` · `/forecast` · `/assistant` |

**Hard constraint:** Platform Core, Ecosystem, Agro Marketplace, and Port ERP are not modified. AI consumes Platform only via bridges.

## Recommendation Engine

Personal · Similar · Alternative · Budget optimization · Ownership cost · Family · Commercial · Fleet

## Pricing AI

Market value · Fair price · Dealer · Wholesale · Retail · Prediction · Trend · Depreciation · Residual value

## Inspection AI

Photo analysis · Damage · Paint · Body alignment · Wheels · Interior · Engine bay · Risk score · Repair estimate

## Buyer Assistant

Natural language search · Q&A · Comparison · Purchase · Negotiation · Finance · Insurance suggestions

## Knowledge & Forecasting

Specs · Common problems · Recalls · Maintenance · Reliability · Fuel · Service intervals  
Future value · Maintenance costs · Repair probability · Insurance risk · Ownership cost · Market demand

```python
from applications.auto_marketplace import auto_marketplace

assert auto_marketplace.config.auto_ai_engine == "1.0"
insight = auto_marketplace.auto_ai.pricing_ai.analyze(base_price=20000, year=2021, mileage_km=30000)
assert insight.fair_price > 0
```

# Business Intelligence & Executive Dashboard

> Sprint 6.6 — real-time analytics, executive dashboards, AI insights, and forecasting

## Overview

Sprint 6.6 delivers a complete **BI Engine** for the Auto Marketplace: role-based executive dashboards, KPIs, multi-domain analytics, forecasting, AI insights, and exportable reports — integrated with Platform Core v3.0 via bridges only.

---

## Architecture

```mermaid
flowchart TB
    subgraph BIEngine
        BE[BIEngine]
        ED[ExecutiveDashboard]
        AE[AnalyticsEngine]
        KPI[KPIService]
        FC[ForecastingService]
        RP[BIReportService]
        AI[AIInsightsService]
    end

    BE --> ED & AE & KPI & FC & RP & AI
    AI -.-> Platform Core
    BE --> CRMEngine
    BE --> FinanceEngine
```

---

## Modules

| Module | Role |
|--------|------|
| `business_intelligence/` | Engine, models, events, security, AI insights |
| `executive_dashboard/` | Role-based dashboards |
| `analytics/` | Multi-domain analytics engine |
| `forecasting/` | Sales, revenue, inventory, demand, cash flow, growth |
| `kpi/` | 12 core KPIs |
| `statistics/` | Aggregate statistics |
| `visualizations/` | Chart data for dashboards |
| `reports/bi_service.py` | Period reports with PDF/Excel/CSV export |

---

## Dashboard Guide

Seven role-based dashboards:

| Role | Dashboard |
|------|-----------|
| Owner | Full KPI grid, sales & financial charts |
| Administrator | Full operational overview |
| Sales Manager | Pipeline, conversion, deal KPIs |
| Dealer | Dealer performance metrics |
| Finance Manager | Revenue, profit, margin |
| Operations | Inventory & workflow metrics |
| AI Agent | Agent analytics & recommendation accuracy |

```python
from applications.auto_marketplace import auto_marketplace

snapshot = await auto_marketplace.bi_engine.dashboard.get_dashboard("owner")
print(snapshot.kpis, snapshot.widgets)
```

---

## Analytics Guide

Domains: sales, financial, customer, inventory, marketing, dealer, workflow, agent

```python
auto_marketplace.bi_engine.analytics.sales_analytics()
auto_marketplace.bi_engine.analytics.financial_analytics()
auto_marketplace.bi_engine.analytics.all_analytics()
```

---

## KPIs

Revenue, Profit, Gross Margin, Vehicle Sales, Lead Conversion, Average Deal Size, Average Sales Cycle, Inventory Turnover, Customer Satisfaction, Dealer Performance, AI Recommendation Accuracy, Agent Performance

```python
kpis = auto_marketplace.bi_engine.kpi.compute_all()
auto_marketplace.bi_engine.kpi.get_kpi("revenue")
```

---

## Forecasting Guide

```python
await auto_marketplace.bi_engine.forecasting.sales_forecast(period_days=30)
await auto_marketplace.bi_engine.forecasting.revenue_forecast()
await auto_marketplace.bi_engine.forecasting.all_forecasts()
```

Types: sales, revenue, inventory, demand, cashflow, growth

---

## AI Insights

| Capability | Description |
|------------|-------------|
| Anomaly detection | Revenue and metric deviations |
| Trend analysis | Time-series direction |
| Opportunity detection | Hot lead clusters |
| Risk detection | Churn and business risks |
| Executive recommendations | Reasoning Engine bridge |
| Predictive alerts | Forecast-based warnings |

---

## Reporting Guide

Periods: daily, weekly, monthly, quarterly, annual, custom

Export formats: PDF, Excel, CSV

```python
report = await auto_marketplace.bi_engine.reports.generate("monthly")
auto_marketplace.bi_engine.reports.export(report.report_id, "pdf")
```

---

## Security — BI Roles

Owner, Administrator, Finance Manager, Sales Manager, Dealer, AI Agent — each with scoped dashboard and report permissions.

---

## Events

`DashboardUpdated`, `BIReportGenerated`, `ForecastCompleted`, `InsightGenerated`, `RiskDetected`, `OpportunityDetected`

---

## API — `/api/auto/v1/bi`

| Method | Path | Description |
|--------|------|-------------|
| GET | `/metrics` | BI metrics |
| GET | `/dashboard/{role}` | Role-based dashboard |
| GET | `/kpis` | All KPIs |
| GET | `/kpis/{name}` | Single KPI |
| GET | `/analytics` | All analytics |
| GET | `/analytics/{domain}` | Domain analytics |
| GET | `/forecast/{type}` | Single forecast |
| GET | `/forecast?type=all` | All forecasts |
| POST | `/reports?period=monthly` | Generate report |
| GET | `/reports/{id}/export?format=pdf` | Export report |
| GET | `/insights` | AI insights |
| GET | `/statistics` | Statistics summary |
| GET | `/charts/{type}` | Chart data |

---

## Manifest

`application_version: "1.5.0-alpha"`

---

## Tests

```bash
pytest tests/test_bi_engine.py -q
```

---

## Developer Guide

Access via `auto_marketplace.bi_engine`. Legacy Sprint 6.1 `analytics_service` remains unchanged.

```python
auto_marketplace.bi_engine.metrics()
auto_marketplace.bi_engine.security.authorize("finance_manager", "dashboard.finance")
auto_marketplace.bi_engine.visualizations.pipeline_chart()
```

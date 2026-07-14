# Marketing Analytics v1 — CPL, conversion, revenue and ROI by source.

from __future__ import annotations

from decimal import Decimal
from typing import Any

from database.models.marketing_analytics_v1 import (
    MARKETING_SOURCE_DISPLAY,
    MarketingSourceKey,
)
from database.session import get_session
from repositories.marketing_analytics_v1_repository import MarketingAnalyticsV1Repository
from repositories.owner_dashboard_repository import OwnerDashboardRepository


class MarketingAnalyticsV1:
    SOURCE_ALIASES: dict[str, str] = {
        "facebook": MarketingSourceKey.FACEBOOK.value,
        "fb": MarketingSourceKey.FACEBOOK.value,
        "instagram": MarketingSourceKey.INSTAGRAM.value,
        "ig": MarketingSourceKey.INSTAGRAM.value,
        "tiktok": MarketingSourceKey.TIKTOK.value,
        "tt": MarketingSourceKey.TIKTOK.value,
        "telegram": MarketingSourceKey.TELEGRAM.value,
        "tg": MarketingSourceKey.TELEGRAM.value,
        "google": MarketingSourceKey.GOOGLE.value,
        "gclid": MarketingSourceKey.GOOGLE.value,
        "referral": MarketingSourceKey.REFERRAL.value,
        "ref": MarketingSourceKey.REFERRAL.value,
        "boroda": MarketingSourceKey.BORODA_CARS.value,
        "boroda_cars": MarketingSourceKey.BORODA_CARS.value,
        "borodacars": MarketingSourceKey.BORODA_CARS.value,
    }

    @staticmethod
    def resolve_marketing_source(
        *,
        utm_source: str | None = None,
        source_link: str | None = None,
        referral_code: str | None = None,
        referrer: str | None = None,
    ) -> str:
        for value in (utm_source, source_link, referrer, referral_code):
            if not value:
                continue
            lowered = value.strip().lower()
            for token in lowered.replace("-", "_").split("_"):
                if token in MarketingAnalyticsV1.SOURCE_ALIASES:
                    return MarketingAnalyticsV1.SOURCE_ALIASES[token]
            if "boroda" in lowered:
                return MarketingSourceKey.BORODA_CARS.value
            if lowered in MarketingAnalyticsV1.SOURCE_ALIASES:
                return MarketingAnalyticsV1.SOURCE_ALIASES[lowered]

        if referral_code or referrer:
            return MarketingSourceKey.REFERRAL.value
        if utm_source:
            return MarketingSourceKey.OTHER.value
        return MarketingSourceKey.TELEGRAM.value

    @staticmethod
    def display_name(source_key: str | None) -> str:
        if not source_key:
            return MARKETING_SOURCE_DISPLAY[MarketingSourceKey.OTHER.value]
        return MARKETING_SOURCE_DISPLAY.get(
            source_key,
            source_key.replace("_", " ").title(),
        )

    @staticmethod
    async def get_owner_metrics() -> dict[str, Any]:
        month = OwnerDashboardRepository.start_of_month()
        today = OwnerDashboardRepository.start_of_today()

        async with get_session() as session:
            repo = MarketingAnalyticsV1Repository(session)
            costs = await repo.list_source_costs()
            cost_map = {c.source_key: c for c in costs}

            source_metrics_month = await repo.source_metrics(since=month)
            source_metrics_all = await repo.source_metrics()
            campaigns = await repo.campaign_metrics(since=month)
            revenue_by_campaign = await repo.revenue_by_campaign(since=month)
            attribution = await repo.attribution_breakdown(since=month)
            leads_today = await repo.count_leads(since=today)
            leads_month = await repo.count_leads(since=month)

        enriched = MarketingAnalyticsV1._enrich_with_costs(source_metrics_month, cost_map)
        enriched_all = MarketingAnalyticsV1._enrich_with_costs(source_metrics_all, cost_map)

        ranked_roi = [
            row for row in enriched
            if row["leads"] > 0
        ]
        ranked_roi.sort(key=lambda r: r["roi"], reverse=True)
        best = ranked_roi[0] if ranked_roi else None
        worst = ranked_roi[-1] if len(ranked_roi) > 1 else None

        campaign_revenue_map = {
            (camp, src): rev
            for camp, src, rev in revenue_by_campaign
        }
        campaign_rows = []
        for row in campaigns:
            revenue = campaign_revenue_map.get(
                (row["campaign"], row["source_key"]),
                Decimal("0"),
            )
            campaign_rows.append({**row, "revenue": revenue})

        return {
            "leads_today": leads_today,
            "leads_month": leads_month,
            "by_source": enriched,
            "by_source_all_time": enriched_all,
            "by_campaign": campaign_rows,
            "revenue_by_campaign": [
                {
                    "campaign": camp,
                    "source_key": src,
                    "source": MarketingAnalyticsV1.display_name(src),
                    "revenue": rev,
                }
                for camp, src, rev in revenue_by_campaign
            ],
            "attribution": attribution,
            "best_source": best,
            "worst_source": worst,
            "source_costs": [
                {
                    "source_key": c.source_key,
                    "display_name": c.display_name,
                    "cost_per_lead": c.cost_per_lead,
                    "currency": c.currency,
                }
                for c in costs
            ],
        }

    @staticmethod
    def _enrich_with_costs(
        metrics: list[dict],
        cost_map: dict,
    ) -> list[dict]:
        enriched: list[dict] = []
        for row in metrics:
            source_key = row["source_key"]
            cost_row = cost_map.get(source_key) or cost_map.get(MarketingSourceKey.OTHER.value)
            cpl = Decimal(cost_row.cost_per_lead) if cost_row else Decimal("0")
            leads = row["leads"]
            revenue = row["revenue"]
            total_cost = cpl * leads
            roi = (
                round(float((revenue - total_cost) / total_cost) * 100, 1)
                if total_cost > 0
                else (100.0 if revenue > 0 else 0.0)
            )
            enriched.append({
                **row,
                "source": MarketingAnalyticsV1.display_name(source_key),
                "cpl": cpl,
                "total_cost": total_cost,
                "roi": roi,
            })
        enriched.sort(key=lambda r: r["revenue"], reverse=True)
        return enriched

    @staticmethod
    def format_owner_marketing_analytics(data: dict[str, Any]) -> str:
        m = data.get("marketing_v1") or data.get("marketing") or {}
        lines = [
            "📈 Marketing Analytics v1",
            "",
            f"Leads today: {m.get('leads_today', 0)}",
            f"Leads this month: {m.get('leads_month', 0)}",
            "",
            "Metrics by source (month):",
        ]
        for row in m.get("by_source") or []:
            lines.append(
                f"  • {row['source']}: leads {row['leads']}, "
                f"CPL {row['cpl']}, conv {row['conversion_rate']}%, "
                f"rev {row['revenue']}, ROI {row['roi']}%"
            )
        if not m.get("by_source"):
            lines.append("  • —")

        best = m.get("best_source")
        worst = m.get("worst_source")
        lines.append("")
        if best:
            lines.append(
                f"🏆 Best source: {best['source']} (ROI {best['roi']}%, rev {best['revenue']})"
            )
        else:
            lines.append("🏆 Best source: —")
        if worst and worst != best:
            lines.append(
                f"⚠️ Worst source: {worst['source']} (ROI {worst['roi']}%, rev {worst['revenue']})"
            )
        else:
            lines.append("⚠️ Worst source: —")

        lines.append("")
        lines.append("Revenue by campaign (month):")
        for row in m.get("revenue_by_campaign") or []:
            lines.append(
                f"  • {row['campaign']} / {row['source']}: {row['revenue']}"
            )
        if not m.get("revenue_by_campaign"):
            lines.append("  • —")

        lines.append("")
        lines.append("Conversion by campaign (month):")
        for row in m.get("by_campaign") or []:
            lines.append(
                f"  • {row['campaign']} ({row['source_key']}): "
                f"{row['conversion_rate']}% ({row['won']}/{row['leads']}), rev {row.get('revenue', 0)}"
            )
        if not m.get("by_campaign"):
            lines.append("  • —")

        lines.append("")
        lines.append("Attribution (source link / UTM / referrer):")
        for row in m.get("attribution") or []:
            lines.append(
                f"  • link={row.get('source_link') or '—'} "
                f"utm={row.get('utm_source') or '—'}/{row.get('utm_campaign') or '—'}/"
                f"{row.get('utm_medium') or '—'} ref={row.get('referrer') or '—'} "
                f"({row['leads']})"
            )
        if not m.get("attribution"):
            lines.append("  • —")

        lines.append("")
        lines.append("Tracked sources:")
        lines.append("  Facebook, Instagram, TikTok, Telegram, Google, Referral, Boroda Cars")
        return "\n".join(lines)

    @staticmethod
    def lead_attribution_fields(
        *,
        source_link: str | None,
        utm_source: str | None,
        utm_campaign: str | None,
        utm_medium: str | None,
        referral_code: str | None,
    ) -> dict[str, str | None]:
        referrer = referral_code
        marketing_source = MarketingAnalyticsV1.resolve_marketing_source(
            utm_source=utm_source,
            source_link=source_link,
            referral_code=referral_code,
            referrer=referrer,
        )
        return {
            "referrer": referrer,
            "marketing_source": marketing_source,
        }

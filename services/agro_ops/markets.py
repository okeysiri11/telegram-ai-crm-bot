"""AGRO 1.1 — markets, manual/automatic prices, history, landed cost."""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any

from services.agro_ops.finance import COST_FIELDS
from services.agro_ops.rbac import require

TWO = Decimal("0.01")

MARKET_TYPES = [
    ("local", "Местный рынок"),
    ("region", "Регион"),
    ("country", "Страна"),
    ("port", "Порт"),
    ("elevator", "Элеватор"),
    ("exchange", "Биржа"),
    ("buyer", "Покупатель"),
    ("supplier", "Поставщик"),
    ("export", "Экспортный рынок"),
    ("manual", "Ручной рынок"),
]

PRICE_SOURCE_TYPES = [
    ("AUTOMATIC", "АВТО (внешний источник)"),
    ("MANUAL", "MANUAL DATA"),
    ("COUNTERPARTY", "MANUAL DATA · КОНТРАГЕНТ"),
    ("CONTRACT", "MANUAL DATA · ДОГОВОР"),
    ("MARKET_PROVIDER", "ПРОВАЙДЕР"),
]

PRICE_KINDS = [
    ("local_price", "Местная цена"),
    ("buyer_bid", "Заявка покупателя"),
    ("seller_offer", "Предложение продавца"),
    ("freight", "Фрахт"),
    ("warehouse", "Складская цена"),
    ("contract", "Контрактная цена"),
]


def _dec(value: Any) -> Decimal:
    if value in (None, ""):
        return Decimal("0")
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return Decimal("0")


def _money(value: Decimal) -> float:
    return float(value.quantize(TWO, rounding=ROUND_HALF_UP))


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class AgroOpsMarketsMixin:
    """Mixed into AgroOpsService."""

    def normalize_market_item(self, kind: str, item: dict[str, Any]) -> dict[str, Any]:
        if kind == "market":
            item.setdefault("market_type", item.get("type") or item.get("group") or "manual")
            item.setdefault("currency", "UAH")
            item.setdefault("unit", "т")
            item.setdefault("status", "active")
        if kind == "market_price":
            item.setdefault("source_type", "MANUAL")
            item.setdefault("price_kind", item.get("price_kind") or "local_price")
            item.setdefault("currency", "UAH")
            item.setdefault("unit", "т")
            item.setdefault("vat_included", False)
            item.setdefault("valid_from", (item.get("date") or _now())[:10])
            item["price"] = float(_dec(item.get("price")))
            if item.get("is_demo") or str(item.get("data_class") or "") == "demo":
                item["data_class"] = "demo"
                item["is_demo"] = True
            elif str(item.get("source_type") or "MANUAL") in {"MANUAL", "COUNTERPARTY", "CONTRACT"}:
                item["data_class"] = "manual"
                item["manual_label"] = "MANUAL DATA"
                status = str(item.get("manual_status") or "").upper()
                item["manual_status"] = status if status in {"CONFIRMED", "UNCONFIRMED"} else "CONFIRMED"
            if not item.get("name") and not item.get("title"):
                prefix = "DEMO" if item.get("is_demo") else "MANUAL DATA"
                item["name"] = f"{prefix} · {item.get('commodity') or item.get('crop') or 'Цена'} {item['price']} {item['currency']}"
        return item

    async def market_dashboard(self, organization_id: str, role: str | None = None, query: dict[str, str] | None = None) -> dict[str, Any]:
        denied = require(role, "list")
        if denied:
            return denied
        from services.agro_ops.service import _org, active_only

        org = _org(organization_id)
        await self.ensure_hydrated(org)  # type: ignore[attr-defined]
        bag = self._bag(org)  # type: ignore[attr-defined]
        markets = active_only(bag.get("market") or [])
        prices = active_only(bag.get("market_price") or [])
        q = query or {}
        crop = (q.get("crop") or q.get("commodity") or "").strip().lower()
        if crop:
            prices = [p for p in prices if crop in str(p.get("commodity") or p.get("crop") or "").lower()]
        if q.get("market_id"):
            prices = [p for p in prices if str(p.get("market_id")) == q["market_id"]]
        if q.get("country"):
            prices = [p for p in prices if str(p.get("country") or "") == q["country"]]
        if q.get("source_type"):
            prices = [p for p in prices if str(p.get("source_type")) == q["source_type"]]
        prices.sort(key=lambda p: str(p.get("valid_from") or p.get("created_at") or ""), reverse=True)
        latest_by_key: dict[str, dict[str, Any]] = {}
        for p in prices:
            key = f"{p.get('market_id')}|{p.get('commodity') or p.get('crop')}|{p.get('currency')}"
            if key not in latest_by_key:
                latest_by_key[key] = p
        current = []
        for p in latest_by_key.values():
            hist = [
                x for x in prices
                if str(x.get("market_id")) == str(p.get("market_id"))
                and str(x.get("commodity") or x.get("crop")) == str(p.get("commodity") or p.get("crop"))
            ]
            hist.sort(key=lambda x: str(x.get("valid_from") or x.get("created_at") or ""))
            prev = hist[-2]["price"] if len(hist) > 1 else None
            change = None
            if prev not in (None, "") and _dec(p.get("price")):
                change = _money(_dec(p.get("price")) - _dec(prev))
            market = next((m for m in markets if str(m.get("id")) == str(p.get("market_id"))), None)
            current.append(
                {
                    **p,
                    "market_name": (market or {}).get("name") or p.get("market_name") or "—",
                    "change": change,
                    "source_type": p.get("source_type") or "MANUAL",
                    "updated_at": p.get("valid_from") or p.get("created_at"),
                }
            )
        return {
            "ok": True,
            "markets": markets,
            "current": current,
            "history": prices[:200],
            "automatic_available": any(str(p.get("source_type")) in {"AUTOMATIC", "MARKET_PROVIDER"} for p in prices),
        }

    async def price_history(
        self, organization_id: str, role: str | None = None, query: dict[str, str] | None = None
    ) -> dict[str, Any]:
        dash = await self.market_dashboard(organization_id, role, query)
        if not dash.get("ok"):
            return dash
        span = (query or {}).get("span") or "30D"
        days = {"7D": 7, "30D": 30, "3M": 90, "6M": 180, "1Y": 365}.get(span, 30)
        cutoff = datetime.now(timezone.utc).date().toordinal() - days
        points = []
        for p in dash["history"]:
            raw = str(p.get("valid_from") or p.get("created_at") or "")[:10]
            try:
                d = datetime.fromisoformat(raw).date().toordinal()
            except Exception:
                continue
            if d >= cutoff:
                points.append(
                    {
                        "date": raw,
                        "price": p.get("price"),
                        "currency": p.get("currency"),
                        "market_id": p.get("market_id"),
                        "source_type": p.get("source_type"),
                        "source": p.get("source") or p.get("comment"),
                    }
                )
        return {"ok": True, "span": span, "points": points}

    async def compare_markets(self, organization_id: str, body: dict[str, Any], role: str | None = None) -> dict[str, Any]:
        denied = require(role, "list")
        if denied:
            return denied
        dash = await self.market_dashboard(organization_id, role, {"crop": str(body.get("crop") or body.get("commodity") or "")})
        if not dash.get("ok"):
            return dash
        ids = body.get("market_ids") or []
        if isinstance(ids, str):
            ids = [x.strip() for x in ids.split(",") if x.strip()]
        rows = [r for r in dash["current"] if not ids or str(r.get("market_id")) in {str(x) for x in ids}]
        logistics = _dec(body.get("logistics_cost") or body.get("transport"))
        compared = []
        for r in rows:
            price = _dec(r.get("price"))
            delivered = price + logistics
            sale = _dec(body.get("sale_price"))
            margin = sale - delivered if sale else Decimal("0")
            compared.append(
                {
                    **r,
                    "logistics_cost": _money(logistics),
                    "delivered_cost": _money(delivered),
                    "potential_margin": _money(margin) if sale else None,
                    "margin_pct": float((margin / sale * 100).quantize(TWO)) if sale else None,
                }
            )
        return {"ok": True, "items": compared}

    async def landed_cost(self, organization_id: str, body: dict[str, Any], role: str | None = None) -> dict[str, Any]:
        denied = require(role, "finance")
        if denied:
            return denied
        calc = {
            "title": body.get("title") or "Доставленная себестоимость",
            "quantity": body.get("quantity") or 1,
            "purchase_price": body.get("purchase_price") or body.get("price"),
            "sale_price": body.get("sale_price"),
            "currency": body.get("currency") or "UAH",
            "fx_rate": body.get("fx_rate"),
            "deal_id": body.get("deal_id"),
            "counterparty_id": body.get("counterparty_id"),
            "market_id": body.get("market_id"),
            "trip_id": body.get("trip_id"),
        }
        for key, _label in COST_FIELDS:
            if body.get(key) not in (None, ""):
                calc[key] = body[key]
        if body.get("trip_id"):
            from services.agro_ops.service import _org, active_only

            org = _org(organization_id)
            await self.ensure_hydrated(org)  # type: ignore[attr-defined]
            trip = next((t for t in active_only(self._bag(org).get("trip") or []) if str(t.get("id")) == str(body["trip_id"])), None)  # type: ignore[attr-defined]
            if trip and not calc.get("transport"):
                calc["transport"] = trip.get("total_logistics_cost") or trip.get("rate")
        computed = self.compute_calculation(calc)  # type: ignore[attr-defined]
        totals = computed.get("totals") or {}
        qty = _dec(computed.get("quantity"))
        delivered = _dec(totals.get("total_cost"))
        sale = _dec(totals.get("sale_value"))
        margin = sale - delivered if sale else Decimal("0")
        computed["delivered_cost"] = _money(delivered)
        computed["margin_per_tonne"] = _money(margin / qty) if qty else 0
        computed["total_margin"] = _money(margin)
        computed["margin_pct"] = totals.get("margin_pct")
        return {"ok": True, "item": computed}

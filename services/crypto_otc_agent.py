# CryptoOTCAgent — fee, profit, routes, liquidity, deal history.


class CryptoOTCAgent:
    MODULE = "crypto_otc"
    DEFAULT_FEE_RATE = 0.005
    CASH_FEE_RATE = 0.01
    ROUTES = {
        "BUY_USDT": ("bank_transfer", "p2p", "otc_desk"),
        "SELL_USDT": ("otc_desk", "p2p", "bank_transfer"),
        "BUY_CASH": ("office_pickup", "courier"),
        "SELL_CASH": ("office_deposit", "courier"),
    }

    @staticmethod
    def calculate_fee(amount: float, direction: str = "BUY_USDT", rate: float = None) -> float:
        amt = float(amount or 0)
        if amt <= 0:
            return 0.0
        rate_pct = CryptoOTCAgent.CASH_FEE_RATE if "CASH" in (direction or "") else CryptoOTCAgent.DEFAULT_FEE_RATE
        fee = amt * rate_pct
        if rate and rate > 0:
            fee = max(fee, amt * rate * 0.001)
        return round(fee, 2)

    @staticmethod
    def analyze_profit(deal_id: int) -> dict:
        from database import get_crypto_deal

        deal = get_crypto_deal(deal_id)
        if not deal:
            return {"error": "deal not found"}
        amount = deal[5] or 0
        fee = deal[8] or 0
        rate = deal[7] or 1.0
        gross = amount * rate
        profit = fee
        margin_pct = round((fee / gross * 100), 2) if gross else 0
        return {
            "deal_id": deal_id,
            "amount": amount,
            "fee": fee,
            "gross": round(gross, 2),
            "profit": round(profit, 2),
            "margin_pct": margin_pct,
        }

    @staticmethod
    def recommend_routes(direction: str, amount: float = None, asset: str = "USDT") -> list[str]:
        routes = list(CryptoOTCAgent.ROUTES.get(direction, ("otc_desk",)))
        if amount and amount >= 100000:
            return routes[:1] + ["compliance_review"]
        return routes

    @staticmethod
    def check_liquidity(asset: str = "USDT") -> dict:
        from database import cursor

        cursor.execute(
            """
            SELECT COUNT(*), COALESCE(SUM(amount), 0)
            FROM crypto_deals
            WHERE asset = ? AND status IN ('NEW', 'PAYMENT_PENDING', 'PROCESSING')
            """,
            (asset,),
        )
        open_count, open_volume = cursor.fetchone()
        available = max(1_000_000 - (open_volume or 0), 0)
        status = "OK" if available > 100000 else "LOW"
        return {
            "asset": asset,
            "open_deals": open_count,
            "open_volume": open_volume or 0,
            "available_liquidity": round(available, 2),
            "status": status,
        }

    @staticmethod
    def get_deal_history(user_id: int, limit: int = 10) -> list[dict]:
        from database import get_crypto_deals, CRYPTO_OTC_DIRECTIONS

        rows = get_crypto_deals(user_id, limit=limit)
        history = []
        for row in rows:
            did, client_id, direction, asset, amount, currency, rate, fee, mgr, status, pay_st, created, updated, closed = row
            history.append({
                "deal_id": did,
                "direction": CRYPTO_OTC_DIRECTIONS.get(direction, direction),
                "amount": amount,
                "asset": asset,
                "status": status,
                "payment_status": pay_st,
                "created_at": created,
            })
        return history

    @staticmethod
    def format_agent_report(user_id: int) -> str:
        liq = CryptoOTCAgent.check_liquidity("USDT")
        history = CryptoOTCAgent.get_deal_history(user_id, limit=5)
        lines = [
            "🤖 CryptoOTCAgent\n",
            f"💧 Ликвидность USDT: {liq['available_liquidity']} ({liq['status']})",
            f"   Открытых сделок: {liq['open_deals']} · объём {liq['open_volume']}\n",
            "📜 История сделок:",
        ]
        if not history:
            lines.append("  · нет данных")
        else:
            for h in history:
                lines.append(
                    f"  · #{h['deal_id']} {h['direction']} {h['amount']} {h['asset']} · {h['status']}"
                )
        return "\n".join(lines)

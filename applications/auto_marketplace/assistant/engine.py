# AI Buyer Assistant — NL search, Q&A, compare, negotiate/finance/insurance tips.

from __future__ import annotations

import re
import uuid

from applications.auto_marketplace.ai.models import AssistantReply
from applications.auto_marketplace.matching.engine import MatchingEngine, matching_engine
from applications.auto_marketplace.shared.store import MarketplaceStore, marketplace_store


class BuyerAssistantEngine:
    def __init__(
        self,
        store: MarketplaceStore | None = None,
        matching: MatchingEngine | None = None,
    ) -> None:
        self._store = store or marketplace_store
        self._matching = matching or matching_engine

    def _intent(self, query: str) -> str:
        q = query.lower()
        if any(w in q for w in ("compare", "vs", "versus")):
            return "compare"
        if any(w in q for w in ("negotiat", "offer", "deal")):
            return "negotiation"
        if any(w in q for w in ("financ", "loan", "lease")):
            return "finance"
        if any(w in q for w in ("insur",)):
            return "insurance"
        if any(w in q for w in ("recommend", "suggest", "buy")):
            return "purchase"
        if any(w in q for w in ("find", "search", "show", "looking")):
            return "search"
        return "question"

    def ask(self, query: str, *, session_id: str = "", budget: float | None = None) -> AssistantReply:
        intent = self._intent(query)
        session_id = session_id or str(uuid.uuid4())
        suggestions: list[str] = []
        vehicles: list[dict] = []
        answer = ""

        if intent == "search":
            make_match = re.search(r"\b(toyota|honda|bmw|ford|kia|nissan|mercedes|audi)\b", query, re.I)
            prefs = {"budget_max": budget or 50000}
            if make_match:
                prefs["make"] = make_match.group(1)
            vehicles = [m.get("vehicle") or {"vehicle_id": m["vehicle_id"]} for m in self._matching.match_preferences(prefs)]
            answer = f"Found {len(vehicles)} vehicles matching your search."
            suggestions = ["Compare top 2", "Check financing options", "Schedule test drive"]
        elif intent == "compare":
            answer = "Compare by price, mileage, reliability, and ownership cost. Prefer lower risk score and residual value."
            suggestions = ["Run pricing AI", "Run inspection AI", "Ask for negotiation tips"]
        elif intent == "negotiation":
            answer = "Start 5–8% below asking price if market trend is declining; emphasize inspection findings."
            suggestions = ["Generate counter offer", "Check wholesale vs retail gap"]
        elif intent == "finance":
            answer = "Consider loan vs lease: loans suit long ownership; leases lower monthly cost with mileage limits."
            suggestions = ["Estimate monthly payment", "Check insurance risk"]
        elif intent == "insurance":
            answer = "Insurance premiums rise with vehicle risk score, age, and accident history."
            suggestions = ["Run risk score", "Compare safer alternatives"]
        elif intent == "purchase":
            vehicles = [m.get("vehicle") or {"vehicle_id": m["vehicle_id"]} for m in self._matching.match_preferences({"budget_max": budget or 40000})]
            answer = "Based on your query, here are purchase recommendations within budget."
            suggestions = ["Optimize budget", "Family recommendations", "Fleet recommendations"]
        else:
            answer = "I can help with search, comparisons, pricing, financing, insurance, and negotiation."
            suggestions = ["Search SUVs under 30000", "Compare two vehicles", "Explain financing"]

        reply = AssistantReply(
            session_id=session_id,
            query=query,
            intent=intent,
            answer=answer,
            suggestions=suggestions,
            vehicles=vehicles[:5],
        )
        return self._store.assistant_replies.save(reply.reply_id, reply)

    def metrics(self) -> dict:
        return {"assistant_replies": self._store.assistant_replies.count()}


buyer_assistant_engine = BuyerAssistantEngine()

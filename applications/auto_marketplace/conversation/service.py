# Conversation service — memory, summarization, sentiment, translation.

from __future__ import annotations

import time
from typing import Any

from events.publisher import publish

from applications.auto_marketplace.ai_sales.events import ConversationSummarizedEvent
from applications.auto_marketplace.ai_sales.integration import ai_sales_platform_bridge
from applications.auto_marketplace.ai_sales.models import (
    ConversationChannel,
    ConversationSession,
    ConversationTurn,
    Sentiment,
)
from applications.auto_marketplace.shared.store import MarketplaceStore, marketplace_store


class ConversationService:
    def __init__(self, store: MarketplaceStore | None = None) -> None:
        self._store = store or marketplace_store

    def get_session(self, session_id: str) -> ConversationSession | None:
        return self._store.conversation_sessions.get(session_id)

    def list_sessions(self, customer_id: str | None = None) -> list[ConversationSession]:
        sessions = self._store.conversation_sessions.list_all()
        if customer_id:
            return [s for s in sessions if s.customer_id == customer_id]
        return sessions

    async def start_session(
        self,
        customer_id: str,
        *,
        channel: ConversationChannel = ConversationChannel.CHAT,
        agent_type: str = "customer_assistant",
    ) -> ConversationSession:
        from applications.auto_marketplace.ai_sales.models import AgentType

        session = ConversationSession(
            customer_id=customer_id,
            channel=channel,
            agent_type=AgentType(agent_type) if agent_type in {a.value for a in AgentType} else AgentType.CUSTOMER_ASSISTANT,
        )
        self._store.conversation_sessions.save(session.session_id, session)
        return session

    async def append_turn(
        self,
        session_id: str,
        *,
        role: str,
        content: str,
        channel: ConversationChannel | None = None,
    ) -> ConversationSession:
        session = self._store.conversation_sessions.get(session_id)
        if session is None:
            raise ValueError(f"Session not found: {session_id}")
        turn = ConversationTurn(
            role=role,
            content=content,
            channel=channel or session.channel,
        )
        session.turns.append(turn)
        session.updated_at = time.time()
        session.sentiment = self.analyze_sentiment(session.turns)
        self._store.conversation_sessions.save(session_id, session)
        await ai_sales_platform_bridge.remember_conversation(
            session.customer_id,
            session_id,
            {"turns": [t.to_dict() for t in session.turns[-5:]]},
        )
        return session

    async def summarize(self, session_id: str) -> str:
        session = self._store.conversation_sessions.get(session_id)
        if session is None:
            return "No session found."
        if not session.turns:
            session.summary = "No conversation yet."
        else:
            texts = [f"{t.role}: {t.content}" for t in session.turns[-10:]]
            summary = " | ".join(texts)[:600]
            analysis = await ai_sales_platform_bridge.reason(
                "Summarize customer conversation",
                {"turns": [t.to_dict() for t in session.turns[-10:]]},
            )
            session.summary = str(analysis.get("summary", summary))
        session.updated_at = time.time()
        self._store.conversation_sessions.save(session_id, session)
        await publish(
            ConversationSummarizedEvent(
                session_id=session_id,
                customer_id=session.customer_id,
                summary=session.summary,
            )
        )
        return session.summary

    async def suggest_response(self, session_id: str) -> dict[str, Any]:
        session = self._store.conversation_sessions.get(session_id)
        if session is None or not session.turns:
            return {"suggestion": "Hello! How can I help you find your next vehicle?"}
        last = session.turns[-1].content.lower()
        if "price" in last or "cost" in last:
            return {"suggestion": "I can share pricing options and financing estimates for this model."}
        if "test drive" in last:
            return {"suggestion": "Would you like to schedule a test drive this week?"}
        return {"suggestion": "Tell me more about your preferred make, budget, and features."}

    @staticmethod
    def analyze_sentiment(turns: list[ConversationTurn]) -> Sentiment:
        if not turns:
            return Sentiment.NEUTRAL
        text = " ".join(t.content.lower() for t in turns[-5:])
        negative = sum(1 for w in ("bad", "expensive", "unhappy", "problem") if w in text)
        positive = sum(1 for w in ("great", "love", "perfect", "thanks", "interested") if w in text)
        if positive > negative:
            return Sentiment.POSITIVE
        if negative > positive:
            return Sentiment.NEGATIVE
        return Sentiment.NEUTRAL

    async def translate(self, text: str, target_language: str = "en") -> dict[str, str]:
        return {"original": text, "translated": text, "target_language": target_language}

    def multi_channel_context(self, customer_id: str) -> dict[str, Any]:
        sessions = self.list_sessions(customer_id)
        channels = {s.channel.value for s in sessions}
        all_turns = [t.to_dict() for s in sessions for t in s.turns[-3:]]
        return {
            "customer_id": customer_id,
            "channels": sorted(channels),
            "recent_turns": all_turns[-15:],
            "session_count": len(sessions),
        }


conversation_service = ConversationService()

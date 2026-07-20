# CommunicationService — phone calls and emails.

from __future__ import annotations

from applications.auto_marketplace.activities.service import ActivityService, activity_service
from applications.auto_marketplace.crm.ai_assistant import AISalesAssistant, ai_sales_assistant
from applications.auto_marketplace.crm.models import EmailMessage, Interaction, InteractionType, PhoneCall
from applications.auto_marketplace.shared.store import MarketplaceStore, marketplace_store


class CommunicationService:
    def __init__(
        self,
        store: MarketplaceStore | None = None,
        activities: ActivityService | None = None,
        ai: AISalesAssistant | None = None,
    ) -> None:
        self._store = store or marketplace_store
        self._activities = activities or activity_service
        self._ai = ai or ai_sales_assistant

    async def log_call(self, call: PhoneCall) -> PhoneCall:
        saved = self._store.phone_calls.save(call.call_id, call)
        interactions = [i.to_dict() for i in self._store.interactions.list_all() if i.customer_id == call.customer_id]
        saved.summary = await self._ai.summarize_conversation(interactions)
        self._activities.log_interaction(
            Interaction(
                customer_id=call.customer_id,
                interaction_type=InteractionType.CALL,
                subject=f"Phone call ({call.direction})",
                body=saved.summary,
                agent_id=call.agent_id,
            )
        )
        return self._store.phone_calls.save(call.call_id, saved)

    def log_email(self, email: EmailMessage) -> EmailMessage:
        saved = self._store.email_messages.save(email.email_id, email)
        self._activities.log_interaction(
            Interaction(
                customer_id=email.customer_id,
                interaction_type=InteractionType.EMAIL,
                subject=email.subject,
                body=email.body,
                agent_id=email.agent_id,
            )
        )
        return saved


communication_service = CommunicationService()

# Communication Hub v1 — unified inbox, routing, attribution, auto-response, escalation.

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select

from config import MANAGER_ID, OWNER_ID
from database.models.audit_log import AuditAction
from database.models.communication_hub import (
    CommunicationMessage,
    HubCampaignStatus,
    HubChannelType,
    HubMessageDirection,
    HubMessageStatus,
    HubSenderType,
)
from database.models.notification import NotificationChannel, NotificationType
from database.models.ai_sales_agent import SalesLeadSource
from database.session import get_session
from repositories.audit_repository import AuditRepository
from repositories.communication_hub_repository import (
    CommunicationCampaignRepository,
    CommunicationChannelRepository,
    CommunicationMessageRepository,
)
from repositories.notification_repository import NotificationRepository
from repositories.user_role_repository import UserRoleRepository
from services.pg_ai_sales_agent_engine import AiSalesAgentV1
from services.pg_partner_tenant_engine import PartnerTenantEngineV1

COMMUNICATION_HUB_ROLES = frozenset({"OWNER", "ADMIN", "MANAGER"})
ESCALATION_KEYWORDS = (
    "manager", "human", "complaint", "urgent", "менеджер", "оператор", "жалоб",
)

DEFAULT_AUTO_RESPONSES: dict[str, str] = {
    HubChannelType.TELEGRAM.value: "Thanks for reaching out! A specialist will assist you shortly.",
    HubChannelType.INSTAGRAM.value: "Hi! We received your message and will reply soon.",
    HubChannelType.FACEBOOK.value: "Hello! Thanks for contacting us — we'll get back to you shortly.",
    HubChannelType.TIKTOK.value: "Thanks for your interest! Our team will follow up soon.",
    HubChannelType.WEBSITE_CHAT.value: "Welcome! How can we help you find your next vehicle?",
}


class CommunicationHubError(Exception):
    pass


class CommunicationHubV1:
    @staticmethod
    async def user_can_access(user_id: int) -> bool:
        if user_id == OWNER_ID:
            return True
        async with get_session() as session:
            roles = await UserRoleRepository(session).get_user_roles(user_id)
            return any(role.code in COMMUNICATION_HUB_ROLES for role in roles)

    @staticmethod
    async def _require_access(actor_id: int, tenant_id: uuid.UUID):
        if not await CommunicationHubV1.user_can_access(actor_id):
            raise CommunicationHubError("Communication hub access denied")
        return await PartnerTenantEngineV1.resolve_context(actor_id, tenant_id)

    @staticmethod
    def _channel_snapshot(row) -> dict[str, Any]:
        return {
            "id": str(row.id),
            "tenant_id": str(row.tenant_id),
            "channel_type": row.channel_type,
            "external_id": row.external_id,
            "name": row.name,
            "is_active": row.is_active,
            "config": row.config or {},
        }

    @staticmethod
    def _message_snapshot(row) -> dict[str, Any]:
        return {
            "id": str(row.id),
            "channel_id": str(row.channel_id),
            "conversation_id": row.conversation_id,
            "direction": row.direction,
            "sender_type": row.sender_type,
            "sender_id": row.sender_id,
            "message_text": row.message_text,
            "status": row.status,
            "sales_lead_id": str(row.sales_lead_id) if row.sales_lead_id else None,
            "automation_lead_id": str(row.automation_lead_id) if row.automation_lead_id else None,
            "assigned_manager_id": row.assigned_manager_id,
            "campaign_id": str(row.campaign_id) if row.campaign_id else None,
            "created_at": row.created_at.isoformat(),
        }

    @staticmethod
    def _campaign_snapshot(row) -> dict[str, Any]:
        return {
            "id": str(row.id),
            "name": row.name,
            "channel_types": row.channel_types or [],
            "message_template": row.message_template,
            "auto_response_enabled": row.auto_response_enabled,
            "routing_rules": row.routing_rules or {},
            "status": row.status,
        }

    @staticmethod
    async def register_channel(
        actor_id: int,
        tenant_id: uuid.UUID,
        *,
        channel_type: str,
        external_id: str,
        name: str,
        config: dict | None = None,
    ) -> dict[str, Any]:
        ctx = await CommunicationHubV1._require_access(actor_id, tenant_id)
        if channel_type not in {c.value for c in HubChannelType}:
            raise CommunicationHubError(f"Invalid channel type: {channel_type}")

        async with get_session() as session:
            row = await CommunicationChannelRepository(session).create(
                tenant_id=tenant_id,
                company_id=ctx.company_id,
                channel_type=channel_type,
                external_id=external_id,
                name=name,
                config=config,
            )
            await session.refresh(row)
            return CommunicationHubV1._channel_snapshot(row)

    @staticmethod
    async def create_campaign(
        actor_id: int,
        tenant_id: uuid.UUID,
        *,
        name: str,
        channel_types: list[str],
        message_template: str | None = None,
        auto_response_enabled: bool = True,
        routing_rules: dict | None = None,
        activate: bool = False,
    ) -> dict[str, Any]:
        ctx = await CommunicationHubV1._require_access(actor_id, tenant_id)
        status = HubCampaignStatus.ACTIVE.value if activate else HubCampaignStatus.DRAFT.value
        async with get_session() as session:
            row = await CommunicationCampaignRepository(session).create(
                tenant_id=tenant_id,
                company_id=ctx.company_id,
                name=name,
                channel_types=channel_types,
                message_template=message_template,
                auto_response_enabled=auto_response_enabled,
                routing_rules=routing_rules or {"default_manager_id": MANAGER_ID},
                status=status,
                created_by=actor_id,
            )
            await session.refresh(row)
            return CommunicationHubV1._campaign_snapshot(row)

    @staticmethod
    async def ingest_message(
        actor_id: int,
        tenant_id: uuid.UUID,
        *,
        channel_id: uuid.UUID,
        conversation_id: str,
        message_text: str,
        sender_id: str | None = None,
    ) -> dict[str, Any]:
        ctx = await CommunicationHubV1._require_access(actor_id, tenant_id)
        async with get_session() as session:
            channel = await CommunicationChannelRepository(session).get_by_id(channel_id)
            if channel is None or channel.tenant_id != tenant_id:
                raise CommunicationHubError(f"Channel not found: {channel_id}")

            row = await CommunicationMessageRepository(session).create(
                channel_id=channel_id,
                tenant_id=tenant_id,
                company_id=ctx.company_id,
                conversation_id=conversation_id,
                direction=HubMessageDirection.INBOUND.value,
                sender_type=HubSenderType.CUSTOMER.value,
                sender_id=sender_id,
                message_text=message_text,
                status=HubMessageStatus.NEW.value,
            )
            await session.refresh(row)
            inbound = CommunicationHubV1._message_snapshot(row)

        routed = await CommunicationHubV1.route_message(actor_id, tenant_id, uuid.UUID(inbound["id"]))
        if any(kw in message_text.lower() for kw in ESCALATION_KEYWORDS):
            escalated = await CommunicationHubV1.escalate_to_manager(
                actor_id, tenant_id, uuid.UUID(inbound["id"])
            )
            return {"inbound": inbound, "routing": routed, "escalation": escalated}

        auto = await CommunicationHubV1.auto_respond(actor_id, tenant_id, uuid.UUID(inbound["id"]))
        return {"inbound": inbound, "routing": routed, "auto_response": auto}

    @staticmethod
    async def get_unified_inbox(
        actor_id: int,
        tenant_id: uuid.UUID,
        *,
        status: str | None = None,
        limit: int = 50,
    ) -> dict[str, Any]:
        await CommunicationHubV1._require_access(actor_id, tenant_id)
        async with get_session() as session:
            channels = await CommunicationChannelRepository(session).list_by_tenant(tenant_id)
            messages = await CommunicationMessageRepository(session).list_inbox(
                tenant_id, status=status, limit=limit
            )
        by_channel: dict[str, int] = {}
        for msg in messages:
            by_channel[str(msg.channel_id)] = by_channel.get(str(msg.channel_id), 0) + 1

        return {
            "channels": [CommunicationHubV1._channel_snapshot(c) for c in channels],
            "messages": [CommunicationHubV1._message_snapshot(m) for m in messages],
            "total": len(messages),
            "by_channel": by_channel,
        }

    @staticmethod
    async def route_message(
        actor_id: int,
        tenant_id: uuid.UUID,
        message_id: uuid.UUID,
        *,
        manager_id: int | None = None,
    ) -> dict[str, Any]:
        ctx = await CommunicationHubV1._require_access(actor_id, tenant_id)
        async with get_session() as session:
            result = await session.execute(
                select(CommunicationMessage).where(CommunicationMessage.id == message_id)
            )
            msg = result.scalar_one_or_none()
            if msg is None or msg.tenant_id != tenant_id:
                raise CommunicationHubError(f"Message not found: {message_id}")

            channel = await CommunicationChannelRepository(session).get_by_id(msg.channel_id)
            campaigns = await CommunicationCampaignRepository(session).list_active_for_channel(
                tenant_id, channel.channel_type if channel else HubChannelType.TELEGRAM.value
            )
            rules = (campaigns[0].routing_rules if campaigns else None) or {}
            assigned = manager_id or rules.get("default_manager_id") or MANAGER_ID

            updated = await CommunicationMessageRepository(session).update_fields(
                message_id,
                status=HubMessageStatus.ROUTED.value,
                assigned_manager_id=assigned,
            )
            await session.refresh(updated)
            return {
                "message": CommunicationHubV1._message_snapshot(updated),
                "assigned_manager_id": assigned,
                "campaign_id": str(campaigns[0].id) if campaigns else None,
            }

    @staticmethod
    async def attribute_lead(
        actor_id: int,
        tenant_id: uuid.UUID,
        message_id: uuid.UUID,
        *,
        customer_name: str | None = None,
        customer_phone: str | None = None,
        create_lead: bool = True,
    ) -> dict[str, Any]:
        await CommunicationHubV1._require_access(actor_id, tenant_id)
        sales_lead_id = None
        if create_lead:
            lead = await AiSalesAgentV1.create_lead(
                actor_id,
                tenant_id,
                customer_name=customer_name,
                customer_phone=customer_phone,
                source=SalesLeadSource.TELEGRAM.value,
            )
            sales_lead_id = uuid.UUID(lead["id"])

        async with get_session() as session:
            updated = await CommunicationMessageRepository(session).update_fields(
                message_id,
                sales_lead_id=sales_lead_id,
            )
            if updated is None:
                raise CommunicationHubError(f"Message not found: {message_id}")
            await session.refresh(updated)
            return {
                "message": CommunicationHubV1._message_snapshot(updated),
                "sales_lead_id": str(sales_lead_id) if sales_lead_id else None,
                "integration": "ai_sales_agent",
            }

    @staticmethod
    async def get_conversation_history(
        actor_id: int,
        tenant_id: uuid.UUID,
        conversation_id: str,
        *,
        limit: int = 100,
    ) -> dict[str, Any]:
        await CommunicationHubV1._require_access(actor_id, tenant_id)
        async with get_session() as session:
            messages = await CommunicationMessageRepository(session).list_conversation(
                tenant_id, conversation_id, limit=limit
            )
        return {
            "conversation_id": conversation_id,
            "messages": [CommunicationHubV1._message_snapshot(m) for m in messages],
            "count": len(messages),
        }

    @staticmethod
    async def auto_respond(
        actor_id: int,
        tenant_id: uuid.UUID,
        message_id: uuid.UUID,
    ) -> dict[str, Any]:
        ctx = await CommunicationHubV1._require_access(actor_id, tenant_id)
        async with get_session() as session:
            result = await session.execute(
                select(CommunicationMessage).where(CommunicationMessage.id == message_id)
            )
            msg = result.scalar_one_or_none()
            if msg is None or msg.tenant_id != tenant_id:
                raise CommunicationHubError(f"Message not found: {message_id}")

            channel = await CommunicationChannelRepository(session).get_by_id(msg.channel_id)
            campaigns = await CommunicationCampaignRepository(session).list_active_for_channel(
                tenant_id, channel.channel_type if channel else HubChannelType.TELEGRAM.value
            )

            response_text = DEFAULT_AUTO_RESPONSES.get(
                channel.channel_type if channel else HubChannelType.WEBSITE_CHAT.value,
                DEFAULT_AUTO_RESPONSES[HubChannelType.WEBSITE_CHAT.value],
            )
            if campaigns and campaigns[0].auto_response_enabled and campaigns[0].message_template:
                response_text = campaigns[0].message_template

            try:
                from services.pg_ai_conversation_skills_engine import AiConversationSkillsV1
                skill_response = await AiConversationSkillsV1.generate_skill_response(
                    actor_id,
                    tenant_id,
                    session_ref=msg.conversation_id,
                    user_message=msg.message_text,
                    channel=channel.channel_type if channel else None,
                )
                if skill_response.get("response"):
                    response_text = skill_response["response"]
            except Exception:
                pass

            outbound = await CommunicationMessageRepository(session).create(
                channel_id=msg.channel_id,
                tenant_id=tenant_id,
                company_id=ctx.company_id,
                conversation_id=msg.conversation_id,
                direction=HubMessageDirection.OUTBOUND.value,
                sender_type=HubSenderType.BOT.value,
                message_text=response_text,
                status=HubMessageStatus.REPLIED.value,
                campaign_id=campaigns[0].id if campaigns else None,
            )
            await CommunicationMessageRepository(session).update_fields(
                message_id, status=HubMessageStatus.REPLIED.value
            )
            await session.refresh(outbound)
            return {
                "inbound_message_id": str(message_id),
                "outbound": CommunicationHubV1._message_snapshot(outbound),
            }

    @staticmethod
    async def escalate_to_manager(
        actor_id: int,
        tenant_id: uuid.UUID,
        message_id: uuid.UUID,
        *,
        manager_id: int | None = None,
        reason: str | None = None,
    ) -> dict[str, Any]:
        ctx = await CommunicationHubV1._require_access(actor_id, tenant_id)
        async with get_session() as session:
            result = await session.execute(
                select(CommunicationMessage).where(CommunicationMessage.id == message_id)
            )
            msg = result.scalar_one_or_none()
            if msg is None or msg.tenant_id != tenant_id:
                raise CommunicationHubError(f"Message not found: {message_id}")

            recipient = manager_id or msg.assigned_manager_id or MANAGER_ID
            await CommunicationMessageRepository(session).update_fields(
                message_id,
                status=HubMessageStatus.ESCALATED.value,
                assigned_manager_id=recipient,
            )

            notification = await NotificationRepository(session).create(
                user_id=recipient,
                notification_type=NotificationType.SYSTEM_ALERT.value,
                channel=NotificationChannel.INTERNAL.value,
                title="Communication Hub escalation",
                message=reason or f"Conversation {msg.conversation_id}: {msg.message_text[:200]}",
            )

            await AuditRepository(session).create_log(
                user_id=actor_id,
                company_id=ctx.company_id,
                tenant_id=tenant_id,
                entity_type="communication_message",
                entity_id=str(message_id),
                action=AuditAction.STATUS_CHANGE.value,
                new_value={"escalated_to": recipient},
            )

            return {
                "message_id": str(message_id),
                "manager_id": recipient,
                "notification_id": str(notification.id),
                "status": HubMessageStatus.ESCALATED.value,
            }

    @staticmethod
    async def get_hub_dashboard(
        actor_id: int,
        tenant_id: uuid.UUID,
    ) -> dict[str, Any]:
        inbox = await CommunicationHubV1.get_unified_inbox(actor_id, tenant_id, limit=200)
        by_status: dict[str, int] = {}
        for msg in inbox["messages"]:
            by_status[msg["status"]] = by_status.get(msg["status"], 0) + 1

        return {
            "tenant_id": str(tenant_id),
            "channels": inbox["channels"],
            "channel_types": [c.value for c in HubChannelType],
            "message_count": inbox["total"],
            "messages_by_status": by_status,
            "capabilities": [
                "unified_inbox",
                "message_routing",
                "lead_attribution",
                "conversation_history",
                "auto_response",
                "escalation_to_manager",
            ],
        }

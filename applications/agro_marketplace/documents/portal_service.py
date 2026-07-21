# Document sharing for portal / mobile.

from __future__ import annotations

from events.publisher import publish

from applications.agro_marketplace.portal.events import DocumentSharedEvent
from applications.agro_marketplace.portal.models import SharedDocument
from applications.agro_marketplace.shared.exceptions import ValidationError
from applications.agro_marketplace.shared.store import AgroStore, agro_store


class PortalDocumentsService:
    def __init__(self, store: AgroStore | None = None) -> None:
        self._store = store or agro_store

    async def share(self, share: SharedDocument) -> SharedDocument:
        if not share.document_id or not share.recipient_id:
            raise ValidationError("document_id and recipient_id are required")
        saved = self._store.shared_documents.save(share.share_id, share)
        await publish(
            DocumentSharedEvent(
                share_id=saved.share_id,
                document_id=saved.document_id,
                owner_id=saved.owner_id,
                recipient_id=saved.recipient_id,
            )
        )
        return saved

    def list_shared(self, *, user_id: str | None = None) -> list[SharedDocument]:
        items = self._store.shared_documents.list_all()
        if user_id:
            items = [d for d in items if d.owner_id == user_id or d.recipient_id == user_id]
        return items


portal_documents_service = PortalDocumentsService()

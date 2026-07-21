# In-app messaging for portal and mobile.

from __future__ import annotations

from applications.agro_marketplace.portal.models import Message, MessageThread
from applications.agro_marketplace.shared.exceptions import NotFoundError, ValidationError
from applications.agro_marketplace.shared.store import AgroStore, agro_store


class MessagingService:
    def __init__(self, store: AgroStore | None = None) -> None:
        self._store = store or agro_store

    def create_thread(self, thread: MessageThread) -> MessageThread:
        if len(thread.participants) < 2:
            raise ValidationError("at least two participants required")
        return self._store.message_threads.save(thread.thread_id, thread)

    def get_thread(self, thread_id: str) -> MessageThread:
        thread = self._store.message_threads.get(thread_id)
        if thread is None:
            raise NotFoundError("MessageThread", thread_id)
        return thread

    def list_threads(self, *, user_id: str | None = None) -> list[MessageThread]:
        items = self._store.message_threads.list_all()
        if user_id:
            items = [t for t in items if user_id in t.participants]
        return items

    def send(self, message: Message) -> Message:
        self.get_thread(message.thread_id)
        if not message.body:
            raise ValidationError("body is required")
        return self._store.messages.save(message.message_id, message)

    def list_messages(self, thread_id: str) -> list[Message]:
        self.get_thread(thread_id)
        items = [m for m in self._store.messages.list_all() if m.thread_id == thread_id]
        return sorted(items, key=lambda m: m.created_at)


messaging_service = MessagingService()

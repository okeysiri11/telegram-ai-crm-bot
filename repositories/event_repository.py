# Event repository — publish and query via EventBus.


class EventRepository:
    @staticmethod
    def publish(event_type: str, user_id: int, **kwargs) -> int:
        from events import EventBus
        return EventBus.publish(event_type, user_id, **kwargs)

    @staticmethod
    def replay(event_id: int, user_id: int = None) -> int | None:
        from events import EventBus
        return EventBus.replay(event_id, user_id)

    @staticmethod
    def list_events(**kwargs) -> list:
        from events import EventBus
        return EventBus.list_events(**kwargs)

    @staticmethod
    def get_event(event_id: int):
        from events import EventBus
        return EventBus.get_event(event_id)

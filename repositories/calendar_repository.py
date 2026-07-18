# Calendar repository — data access only (authorization in CalendarService).


class CalendarRepository:
    @staticmethod
    def get(event_id: int, user_id: int):
        from database import get_event

        return get_event(event_id, user_id)

    @staticmethod
    def create(creator_id: int, title: str, start_time: str, **kwargs) -> int:
        from database import create_event

        return create_event(creator_id=creator_id, title=title, start_time=start_time, **kwargs)

    @staticmethod
    def delete(event_id: int, user_id: int) -> bool:
        from database import delete_event

        return delete_event(event_id, user_id)

    @staticmethod
    def today(user_id: int, scope: str = "my", limit: int = 20) -> list:
        from database import get_today_events

        return get_today_events(user_id, scope=scope, limit=limit)

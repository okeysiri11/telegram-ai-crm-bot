# Calendar repository — data access via CalendarService.


class CalendarRepository:
    @staticmethod
    def get(event_id: int, user_id: int):
        from services.calendar_service import CalendarService
        return CalendarService.get_event(event_id, user_id)

    @staticmethod
    def create(creator_id: int, title: str, start_time: str, **kwargs) -> int:
        from services.calendar_service import CalendarService
        return CalendarService.create_event(creator_id, title, start_time, **kwargs)

    @staticmethod
    def delete(event_id: int, user_id: int) -> bool:
        from services.calendar_service import CalendarService
        return CalendarService.delete_event(event_id, user_id)

    @staticmethod
    def today(user_id: int, scope: str = "my", limit: int = 20) -> list:
        from services.calendar_service import CalendarService
        return CalendarService.get_today_events(user_id, scope=scope, limit=limit)

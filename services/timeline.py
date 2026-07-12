# Unified entity timeline engine.


class TimelineService:
    @staticmethod
    def record(
        entity_type: str,
        entity_id: int,
        event_type: str,
        user_id: int = None,
        description: str = None,
    ) -> int:
        from database import record_timeline_event
        return record_timeline_event(
            entity_type, entity_id, event_type, user_id, description,
        )

    @staticmethod
    def get_timeline(entity_type: str, entity_id: int, limit: int = 50) -> list:
        from database import get_timeline
        return get_timeline(entity_type, entity_id, limit=limit)

    @staticmethod
    def format_timeline_text(entity_type: str, entity_id: int, limit: int = 20) -> str:
        events = TimelineService.get_timeline(entity_type, entity_id, limit=limit)
        if not events:
            return "История пуста."
        lines = [f"📜 История {entity_type} #{entity_id}:\n"]
        for ev in reversed(events):
            _eid, _et, _eid2, ev_type, uid, desc, created = ev
            lines.append(f"· [{created}] {ev_type}: {desc or '—'} (user {uid or '—'})")
        return "\n".join(lines)

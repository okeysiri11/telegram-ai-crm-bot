# Event Bus integration test.

from config import OWNER_ID


class EventBusTestService:
    @staticmethod
    def run_integration_test(user_id: int = None) -> dict:
        from database import cursor, list_platform_events
        from events import EventBus, reset_event_bus_for_tests

        uid = user_id or OWNER_ID
        steps = {}
        try:
            reset_event_bus_for_tests()
            import importlib.util
            spec = importlib.util.spec_from_file_location(
                "event_bus_bridge", "services/event_bus_bridge.py",
            )
            bridge = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(bridge)
            bridge.register_default_subscribers()

            before = len(list_platform_events(limit=1000))

            eid = EventBus.publish(
                "AUTO_LEAD_CREATED",
                user_id=uid,
                entity_id=9001,
                payload={"source": "event_bus_test", "model": "Test Car"},
            )
            steps["publish"] = eid

            event = EventBus.get_event(eid)
            steps["logged_status"] = event.status if event else None
            steps["subscribers"] = EventBus.list_subscribers().get("AUTO_LEAD_CREATED", [])

            replay_id = EventBus.replay(eid, uid)
            steps["replay"] = replay_id

            cursor.execute(
                """
                SELECT COUNT(*) FROM audit_log
                WHERE module = 'event_bus'
                  AND action IN ('event_publish', 'event_replay')
                """
            )
            audit_count = cursor.fetchone()[0]
            steps["audit_entries"] = audit_count

            after = len(list_platform_events(limit=1000))
            steps["events_created"] = after - before

            ok = (
                eid > 0
                and event
                and event.status in ("DELIVERED", "PARTIAL")
                and replay_id
                and replay_id != eid
                and audit_count >= 2
                and steps["events_created"] >= 2
            )
            return {"ok": ok, "status": "OK" if ok else "ERROR", "steps": steps}
        except Exception as exc:
            return {"ok": False, "status": "ERROR", "steps": steps, "error": str(exc)}
        finally:
            reset_event_bus_for_tests()
            import importlib.util
            spec = importlib.util.spec_from_file_location(
                "event_bus_bridge", "services/event_bus_bridge.py",
            )
            bridge = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(bridge)
            bridge.register_default_subscribers()

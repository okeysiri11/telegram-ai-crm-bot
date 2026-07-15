"""Unit tests for DI container scaffold."""

def test_container_registers_storage():
    from container import get_container, reset_container

    reset_container()
    c = get_container()
    assert "storage" in c.registry.registered_names()
    assert "notifications" in c.registry.registered_names()


def test_domain_event_types_exist():
    from src.events import LeadCreated, LeadAssigned, LeadClosed, PhotoUploaded

    e = LeadCreated(lead_id="1", request_number="AUTO-0001")
    assert e.event_type == "LeadCreated"

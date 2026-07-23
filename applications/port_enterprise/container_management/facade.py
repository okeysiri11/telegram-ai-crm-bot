"""Container Management Suite facade — Sprint 15.2."""

from __future__ import annotations

from typing import Any

from applications.port_enterprise.config import DEFAULT_CONFIG
from applications.port_enterprise.container_management.containers import (
    ContainerOperations,
    ContainerRegistry,
    YardManagement,
)
from applications.port_enterprise.container_management.equipment import (
    DigitalTwin,
    PortEquipment,
    TerminalAutomation,
)
from applications.port_enterprise.container_management.services import ContainerDashboard, ContainerKnowledge
from applications.port_enterprise.shared.store import PortEnterpriseStore, port_enterprise_store


class ContainerManagementSuite:
    def __init__(self, store: PortEnterpriseStore | None = None) -> None:
        self.store = store or port_enterprise_store
        self.containers = ContainerRegistry(self.store)
        self.operations = ContainerOperations(self.store)
        self.yard = YardManagement(self.store)
        self.equipment = PortEquipment(self.store)
        self.automation = TerminalAutomation(self.store)
        self.twin = DigitalTwin(self.store)
        self.dashboard = ContainerDashboard(self.store)
        self.knowledge = ContainerKnowledge(self.store)

    def bootstrap(self) -> dict[str, Any]:
        c1 = self.containers.register(
            container_number="MSCU1234567", iso_type="40HC", owner="MSC", status="empty"
        )
        c2 = self.containers.register(
            container_number="HLCU7654321", iso_type="20RF", owner="Hapag", status="full"
        )
        self.containers.inspect(c1["container_id"], result="pass", notes="OK")
        self.containers.maintain(c2["container_id"], work="reefer_service")
        self.containers.set_status(c2["container_id"], status="full")

        self.operations.gate_in(c1["container_id"], gate="G2")
        self.operations.reserve(c1["container_id"], party="Forwarder X")
        self.operations.transfer(c1["container_id"], from_slot="TEMP", to_slot="A-01-02-3")
        self.operations.load(c1["container_id"], vessel_id="vsl_boot")
        self.operations.unload(c1["container_id"], vessel_id="vsl_boot")
        self.operations.transship(c1["container_id"], from_vessel="vsl_a", to_vessel="vsl_b")
        self.operations.gate_out(c2["container_id"], gate="G1")

        yard = self.yard.register_yard(name="Yard Alpha", capacity_teu=15000)
        block = self.yard.create_block(yard_id=yard["yard_id"], name="Block A", rows=20, tiers=5)
        slot = self.yard.allocate_slot(
            block_id=block["block_id"], row=1, bay=2, tier=3, container_id=c1["container_id"]
        )
        self.yard.optimize(yard["yard_id"])

        sts = self.equipment.register(name="STS-01", equipment_type="sts", yard_id=yard["yard_id"])
        rtg = self.equipment.register(name="RTG-07", equipment_type="rtg", yard_id=yard["yard_id"])
        self.equipment.register(name="RMG-02", equipment_type="rmg", yard_id=yard["yard_id"])
        self.equipment.register(name="RS-11", equipment_type="reach_stacker", yard_id=yard["yard_id"])
        self.equipment.register(name="SC-03", equipment_type="straddle", yard_id=yard["yard_id"])
        self.equipment.register(name="TT-21", equipment_type="tractor", yard_id=yard["yard_id"])
        self.equipment.register(name="FL-05", equipment_type="forklift", yard_id=yard["yard_id"])
        self.equipment.health(sts["equipment_id"], health_score=88)
        self.equipment.schedule_maintenance(rtg["equipment_id"], due_at="2026-09-01", work="wire_ropes")

        task = self.automation.assign_task(
            equipment_id=rtg["equipment_id"], container_id=c1["container_id"], task_type="stack"
        )
        self.automation.dispatch(rtg["equipment_id"], destination=slot["position"])
        self.automation.route_container(container_id=c1["container_id"])
        ai_opt = self.automation.optimize_yard_ai(yard["yard_id"])
        self.automation.optimize_queue(queue_name="gate_in", depth=12)
        self.automation.optimize_energy(equipment_id=sts["equipment_id"])

        twin = self.twin.create_twin(terminal_name="Container Terminal 1", yard_id=yard["yard_id"])
        self.twin.visualize_equipment(twin["twin_id"])
        self.twin.visualize_containers(twin["twin_id"])
        self.twin.live_yard(twin["twin_id"])
        sim = self.twin.simulate(twin["twin_id"], hours=24)
        fc = self.twin.forecast_capacity(twin["twin_id"], days=7)

        for rtype, key in (
            ("container", c1["container_id"]),
            ("equipment", sts["equipment_id"]),
            ("yard", yard["yard_id"]),
            ("automation", task["task_id"]),
            ("digital_twin", twin["twin_id"]),
        ):
            self.knowledge.publish(registry_type=rtype, key=key, payload={"bootstrap": True})

        dash = self.dashboard.render(dashboard_type="container")
        return {
            "bootstrap": True,
            "container_id": c1["container_id"],
            "yard_id": yard["yard_id"],
            "block_id": block["block_id"],
            "slot_id": slot["slot_id"],
            "equipment_id": sts["equipment_id"],
            "task_id": task["task_id"],
            "ai_optimization_id": ai_opt["optimization_id"],
            "twin_id": twin["twin_id"],
            "simulation_id": sim["simulation_id"],
            "forecast_id": fc["forecast_id"],
            "dashboard_id": dash["dashboard_id"],
            "version": DEFAULT_CONFIG.application_version,
        }

    def status(self) -> dict[str, Any]:
        return {
            "containers": self.containers.status(),
            "operations": self.operations.status(),
            "yard": self.yard.status(),
            "equipment": self.equipment.status(),
            "automation": self.automation.status(),
            "twin": self.twin.status(),
            "dashboard": self.dashboard.status(),
            "knowledge": self.knowledge.status(),
        }


container_management = ContainerManagementSuite()

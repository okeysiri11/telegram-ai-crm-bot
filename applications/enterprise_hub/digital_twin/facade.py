"""Digital Twin Suite facade — Sprint 20.8."""

from __future__ import annotations

from typing import Any

from applications.enterprise_hub.config import DEFAULT_CONFIG
from applications.enterprise_hub.digital_twin.analytics.anomalies import AnomalyAnalytics
from applications.enterprise_hub.digital_twin.analytics.state_metrics import StateMetrics
from applications.enterprise_hub.digital_twin.analytics.utilization import UtilizationAnalytics
from applications.enterprise_hub.digital_twin.entities.ai_agent import AiAgentTwin
from applications.enterprise_hub.digital_twin.entities.asset import AssetTwin
from applications.enterprise_hub.digital_twin.entities.customer import CustomerTwin
from applications.enterprise_hub.digital_twin.entities.custom import CustomTwin
from applications.enterprise_hub.digital_twin.entities.department import DepartmentTwin
from applications.enterprise_hub.digital_twin.entities.employee import EmployeeTwin
from applications.enterprise_hub.digital_twin.entities.equipment import EquipmentTwin
from applications.enterprise_hub.digital_twin.entities.organization import OrganizationTwin
from applications.enterprise_hub.digital_twin.entities.production import ProductionTwin
from applications.enterprise_hub.digital_twin.entities.project import ProjectTwin
from applications.enterprise_hub.digital_twin.entities.supplier import SupplierTwin
from applications.enterprise_hub.digital_twin.entities.vehicle import VehicleTwin
from applications.enterprise_hub.digital_twin.entities.vessel import VesselTwin
from applications.enterprise_hub.digital_twin.entities.warehouse import WarehouseTwin
from applications.enterprise_hub.digital_twin.prediction_context import PredictionContext
from applications.enterprise_hub.digital_twin.relationship_manager import RelationshipManager
from applications.enterprise_hub.digital_twin.snapshot_manager import SnapshotManager
from applications.enterprise_hub.digital_twin.state_manager import StateManager
from applications.enterprise_hub.digital_twin.synchronization.sync_coordinator import SyncCoordinator
from applications.enterprise_hub.digital_twin.timeline import TimelineEngine
from applications.enterprise_hub.digital_twin.twin_engine import TwinEngine
from applications.enterprise_hub.digital_twin.twin_manager import TwinManager
from applications.enterprise_hub.digital_twin.twin_registry import TwinRegistry
from applications.enterprise_hub.digital_twin.visualization import VisualizationLayer
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


class DigitalTwinSuite:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.manager = TwinManager(self.store)
        self.registry = TwinRegistry(self.store)
        self.engine = TwinEngine(self.store)
        self.states = StateManager(self.store)
        self.relationships = RelationshipManager(self.store)
        self.timeline = TimelineEngine(self.store)
        self.snapshots = SnapshotManager(self.store)
        self.predictions = PredictionContext(self.store)
        self.visualization = VisualizationLayer(self.store)
        self.sync = SyncCoordinator(self.store)
        self.state_metrics = StateMetrics(self.store)
        self.utilization = UtilizationAnalytics(self.store)
        self.anomalies = AnomalyAnalytics(self.store)
        self.organization = OrganizationTwin(self.store)
        self.department = DepartmentTwin(self.store)
        self.employee = EmployeeTwin(self.store)
        self.customer = CustomerTwin(self.store)
        self.supplier = SupplierTwin(self.store)
        self.project = ProjectTwin(self.store)
        self.warehouse = WarehouseTwin(self.store)
        self.equipment = EquipmentTwin(self.store)
        self.vehicle = VehicleTwin(self.store)
        self.vessel = VesselTwin(self.store)
        self.production = ProductionTwin(self.store)
        self.asset = AssetTwin(self.store)
        self.ai_agent = AiAgentTwin(self.store)
        self.custom = CustomTwin(self.store)

    def analytics(self) -> dict[str, Any]:
        sm = self.state_metrics.report()
        util = self.utilization.report()
        anom = self.anomalies.report()
        pred = self.predictions.build(horizon="7d")
        return {
            "active_twins": sm.get("active_twins"),
            "total_twins": sm.get("total_twins"),
            "utilization_rate": util.get("utilization_rate"),
            "anomaly_count": anom.get("anomaly_count"),
            "inconsistencies": anom.get("inconsistencies"),
            "prediction_ready": pred.get("ready_for"),
            "state_metrics_id": sm["analytics_id"],
            "utilization_id": util["analytics_id"],
            "anomalies_id": anom["analytics_id"],
            "prediction_context_id": pred["context_id"],
            "changes": len(self.store.edt_states.list_all()),
        }

    def bootstrap(self) -> dict[str, Any]:
        org = self.organization.create(name="Bidex Holdings", owner="ceo", state={"region": "global"})
        dept = self.department.create(name="Operations", owner="coo", state={"headcount": 42})
        emp = self.employee.create(name="Ada Operator", owner="hr", state={"role": "ops"})
        cust = self.customer.create(name="Acme Corp", owner="crm", state={"tier": "enterprise"})
        supp = self.supplier.create(name="Parts Ltd", owner="erp", state={"lead_days": 7})
        proj = self.project.create(name="Harbor Expansion", owner="pmo", state={"phase": "execution"})
        wh = self.warehouse.create(name="WH-01", owner="logistics", state={"utilization": 0.72})
        eq = self.equipment.create(name="Crane-A", owner="ops", state={"utilization": 0.81, "status": "ok"})
        veh = self.vehicle.create(name="Truck-12", owner="fleet", state={"utilization": 0.55})
        ves = self.vessel.create(name="MV Horizon", owner="port", state={"berth": "B3", "utilization": 0.6})
        prod = self.production.create(name="Line-1", owner="plant", state={"utilization": 0.9})
        asset = self.asset.create(name="Container-C1", owner="yard", state={"location": "yard-a"})
        agent = self.ai_agent.create(name="Planning Agent", owner="ai", state={"mode": "active"})
        custom = self.custom.create(name="Contract-X", owner="legal", state={"doc_type": "contract"})

        r1 = self.relationships.link(source_id=org["twin_id"], target_id=dept["twin_id"], kind="contains")
        r2 = self.relationships.link(source_id=dept["twin_id"], target_id=proj["twin_id"], kind="owns")
        r3 = self.relationships.link(source_id=proj["twin_id"], target_id=cust["twin_id"], kind="serves")
        r4 = self.relationships.link(source_id=proj["twin_id"], target_id=supp["twin_id"], kind="supplies")
        r5 = self.relationships.link(source_id=proj["twin_id"], target_id=custom["twin_id"], kind="documents")
        r6 = self.relationships.link(source_id=proj["twin_id"], target_id=agent["twin_id"], kind="controls")
        r7 = self.relationships.link(source_id=dept["twin_id"], target_id=eq["twin_id"], kind="operates")
        r8 = self.relationships.link(source_id=dept["twin_id"], target_id=emp["twin_id"], kind="employs")

        sync1 = self.sync.ingest(
            source="crm", event_type="CustomerUpdated", twin_id=cust["twin_id"], payload={"tier": "strategic"}
        )
        sync2 = self.sync.ingest(
            source="erp", event_type="OrderCreated", twin_id=asset["twin_id"], payload={"order_id": "O-100"}
        )
        sync3 = self.sync.ingest(
            source="workflow", event_type="TaskCompleted", twin_id=proj["twin_id"], payload={"task": "permit"}
        )
        sync4 = self.sync.ingest(
            source="ai", event_type="AgentDecision", twin_id=agent["twin_id"], payload={"decision": "reschedule"}
        )
        self.timeline.append(
            twin_id=agent["twin_id"], event="ai_decision", actor="ai", detail={"decision": "reschedule"}, ai_decision=True
        )

        conflict = self.sync.conflicts.resolve(
            twin_id=eq["twin_id"],
            local_state={"utilization": 0.81},
            remote_state={"utilization": 0.88, "status": "ok"},
            strategy="merge",
        )
        cons = self.sync.consistency.check()

        snap_a = self.snapshots.capture(kind="automatic", label="boot-a")
        self.engine.update(twin_id=eq["twin_id"], state={"utilization": 0.95}, actor="sensor")
        snap_b = self.snapshots.capture(kind="manual", label="boot-b")
        cmp = self.snapshots.compare(snapshot_a=snap_a["snapshot_id"], snapshot_b=snap_b["snapshot_id"])
        exported = self.snapshots.export(snapshot_id=snap_b["snapshot_id"])

        viz = self.visualization.render(view="dependencies", root_id=org["twin_id"])
        pred = self.predictions.build(horizon="14d")
        analytics = self.analytics()

        return {
            "bootstrap": True,
            "org_id": org["twin_id"],
            "twin_ids": [
                org["twin_id"], dept["twin_id"], emp["twin_id"], cust["twin_id"], supp["twin_id"],
                proj["twin_id"], wh["twin_id"], eq["twin_id"], veh["twin_id"], ves["twin_id"],
                prod["twin_id"], asset["twin_id"], agent["twin_id"], custom["twin_id"],
            ],
            "relationship_ids": [r1["relationship_id"], r2["relationship_id"], r3["relationship_id"], r4["relationship_id"], r5["relationship_id"], r6["relationship_id"], r7["relationship_id"], r8["relationship_id"]],
            "sync_ids": [sync1["update_id"], sync2["update_id"], sync3["update_id"], sync4["update_id"]],
            "conflict_id": conflict["conflict_id"],
            "consistency_ok": cons["consistent"],
            "snapshot_a": snap_a["snapshot_id"],
            "snapshot_b": snap_b["snapshot_id"],
            "compare_delta": cmp["delta"],
            "export_label": exported["label"],
            "visualization_id": viz["visualization_id"],
            "prediction_context_id": pred["context_id"],
            "analytics": analytics,
            "version": DEFAULT_CONFIG.application_version,
        }

    def status(self) -> dict[str, Any]:
        return {
            "manager": self.manager.status(),
            "sync": self.sync.status(),
            "visualization": self.visualization.status(),
            "predictions": self.predictions.status(),
        }


digital_twin = DigitalTwinSuite()

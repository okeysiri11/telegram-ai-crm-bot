# AIOSApplication — AI Operating System (Sprint 12.4).

from __future__ import annotations

from typing import Any

from applications.ai_os.bus import SystemBus, system_bus
from applications.ai_os.config import AIOSConfig, DEFAULT_CONFIG
from applications.ai_os.kernel import AIKernel, ai_kernel
from applications.ai_os.memory import MemoryManager, memory_manager
from applications.ai_os.process import ProcessManager, process_manager
from applications.ai_os.runtime import AIRuntime, ai_runtime
from applications.ai_os.services import (
    AICommunication,
    EnterpriseAIOS,
    Observability,
    ai_communication,
    enterprise_ai_os,
    observability,
)
from applications.ai_os.shared.store import AIOSStore, ai_os_store


class AIOSApplication:
    def __init__(
        self,
        *,
        config: AIOSConfig | None = None,
        store: AIOSStore | None = None,
        kernel: AIKernel | None = None,
        processes: ProcessManager | None = None,
        bus: SystemBus | None = None,
        memory: MemoryManager | None = None,
        runtime: AIRuntime | None = None,
        communication: AICommunication | None = None,
        enterprise: EnterpriseAIOS | None = None,
        observability_svc: Observability | None = None,
    ) -> None:
        self.config = config or DEFAULT_CONFIG
        self.store = store or ai_os_store
        self.kernel = kernel or ai_kernel
        self.processes = processes or process_manager
        self.bus = bus or system_bus
        self.memory = memory or memory_manager
        self.runtime = runtime or ai_runtime
        self.communication = communication or ai_communication
        self.enterprise = enterprise or enterprise_ai_os
        self.observability = observability_svc or observability

    def reset(self) -> None:
        self.store.reset()
        self.kernel._booted = False

    def bootstrap(self) -> dict[str, Any]:
        boot = self.kernel.boot()
        proc = self.processes.start_process(name="aios-supervisor", kind="background_service")
        self.bus.publish(bus="event", topic="ai_os.boot", payload={"version": self.config.application_version})
        self.memory.put(tier="global", key="boot", value={"ok": True})
        cluster = self.enterprise.create_cluster(name="primary", region="global", nodes=3)
        self.observability.log(level="info", message="AI OS bootstrapped")
        self.observability.metric(name="boot_count", value=1)
        return {
            "bootstrap": True,
            "kernel": boot,
            "supervisor": proc["process_id"],
            "cluster_id": cluster["cluster_id"],
            "version": self.config.application_version,
        }

    def health(self) -> dict[str, Any]:
        return {
            "status": "ok",
            "application": self.config.application,
            "application_name": self.config.application_name,
            "application_version": self.config.application_version,
            "release_status": self.config.release_status,
            "api_prefix": self.config.api_prefix,
            "ai_operating_system_ready": True,
            "ai_kernel_ready": True,
            "unified_runtime_ready": True,
            "enterprise_ai_os_ready": True,
            "engines": {
                "ai_kernel": self.config.ai_kernel,
                "process_manager": self.config.process_manager,
                "system_bus": self.config.system_bus,
                "memory_management": self.config.memory_management,
                "ai_runtime": self.config.ai_runtime,
                "ai_communication": self.config.ai_communication,
                "enterprise": self.config.enterprise,
                "observability": self.config.observability,
            },
            "kernel": self.kernel.status(),
            "processes": self.processes.status(),
            "bus": self.bus.status(),
            "memory": self.memory.status(),
            "runtime": self.runtime.status(),
            "communication": self.communication.status(),
            "enterprise": self.enterprise.status(),
            "observability": self.observability.status(),
        }


ai_os = AIOSApplication()

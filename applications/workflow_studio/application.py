# WorkflowStudioApplication — Visual Workflow Studio (Sprint 12.2).

from __future__ import annotations

from typing import Any

from applications.workflow_studio.ai_builder import AIFlowBuilder, ai_flow_builder
from applications.workflow_studio.config import DEFAULT_CONFIG, WorkflowStudioConfig
from applications.workflow_studio.editor import VisualEditor, visual_editor
from applications.workflow_studio.engine import FlowEngine, flow_engine
from applications.workflow_studio.services import (
    BusinessTemplates,
    EnterpriseWorkflow,
    WorkflowMonitoring,
    business_templates,
    enterprise_workflow,
    workflow_monitoring,
)
from applications.workflow_studio.shared.store import WorkflowStudioStore, workflow_studio_store


class WorkflowStudioApplication:
    def __init__(
        self,
        *,
        config: WorkflowStudioConfig | None = None,
        store: WorkflowStudioStore | None = None,
        editor: VisualEditor | None = None,
        engine: FlowEngine | None = None,
        ai_builder: AIFlowBuilder | None = None,
        templates: BusinessTemplates | None = None,
        enterprise: EnterpriseWorkflow | None = None,
        monitoring: WorkflowMonitoring | None = None,
    ) -> None:
        self.config = config or DEFAULT_CONFIG
        self.store = store or workflow_studio_store
        self.editor = editor or visual_editor
        self.engine = engine or flow_engine
        self.ai_builder = ai_builder or ai_flow_builder
        self.templates = templates or business_templates
        self.enterprise = enterprise or enterprise_workflow
        self.monitoring = monitoring or workflow_monitoring

    def reset(self) -> None:
        self.store.reset()

    def health(self) -> dict[str, Any]:
        return {
            "status": "ok",
            "application": self.config.application,
            "application_name": self.config.application_name,
            "application_version": self.config.application_version,
            "release_status": self.config.release_status,
            "api_prefix": self.config.api_prefix,
            "workflow_studio_ready": True,
            "ai_flow_builder_ready": True,
            "visual_automation_ready": True,
            "enterprise_workflow_platform_ready": True,
            "engines": {
                "visual_editor": self.config.visual_editor,
                "flow_engine": self.config.flow_engine,
                "ai_builder": self.config.ai_builder,
                "business_templates": self.config.business_templates,
                "enterprise": self.config.enterprise,
                "monitoring": self.config.monitoring,
            },
            "editor": self.editor.status(),
            "engine": self.engine.status(),
            "ai_builder": self.ai_builder.status(),
            "templates": self.templates.status(),
            "enterprise": self.enterprise.status(),
            "monitoring": self.monitoring.status(),
        }


workflow_studio = WorkflowStudioApplication()

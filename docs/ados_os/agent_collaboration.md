# Agent Collaboration

All communication passes through the AI Orchestrator.

Example CRM flow:

Architect → Research → Business → Developer → QA → Reviewer

Implemented by `CollaborationEngine` using workflow templates and `orchestrator.runAgent()` per step. Shared context carries intermediate results and artifacts.

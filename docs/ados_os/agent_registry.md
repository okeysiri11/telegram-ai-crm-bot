# Agent Registry

Seven collaboration agents auto-register at Orchestrator boot:

Developer · Research · Business · Architect · Reviewer · QA · Automation

Each exposes: id, name, role, provider, skills, status (Idle/Running/Busy/Waiting/Offline/Error), health, queue, metrics, memory, version, last execution.

Agents never call each other — only the AI Orchestrator dispatches work.

# Shared Memory

`SharedWorkflowContext` is the enterprise memory for one collaboration workflow.

Agents (via Orchestrator) can read/append:

- intermediate results
- artifacts / files metadata
- prompts
- decisions
- logs

REST: `GET /memory`, `GET /memory/:workflowId`

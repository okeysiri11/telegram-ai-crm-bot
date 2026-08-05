# Provider Gateway

External AI providers are reached only through Provider Gateway.

Mocks: Cursor · OpenAI · Claude · GitHub Copilot · Local LLM · Mock

Contract: `connect` · `disconnect` · `execute` · `cancel` · `health` · `capabilities` · `configuration`

Orchestrator selects providers by capability — agents never import adapters.

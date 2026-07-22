# Drone AI

Chief Drone AI orchestrates specialist agents through the Platform Multi-Agent Engine:

- Engineering AI
- Firmware AI
- Mission AI
- Manufacturing AI
- Maintenance AI
- Fleet AI
- Cloud AI
- Documentation AI
- Knowledge AI

## API

- `GET /api/drone/v1/ai` — capabilities
- `POST /api/drone/v1/ai/assist` — `{ "agent": "multi_agent_collaborate", "query": "...", "context": { "agents": ["engineering", "mission", "fleet"] } }`

Policy: engineering assistance only.

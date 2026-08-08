# Hercules Workers

Default workers (seeded):

| ID | Kind | GPU |
|----|------|-----|
| w-universal | universal | no |
| w-image | image | yes |
| w-video | video | yes |
| w-voice | voice | no |
| w-llm | llm | no |
| w-telegram | telegram | no |
| w-crm | crm | no |
| w-erp | erp | no |
| w-automation | automation | no |
| w-background | background | no |

Selection: least-load matching kind; GPU workers preferred when `gpu_required`.

Heartbeat: `worker_registry.heartbeat(worker_id, load=…)`.

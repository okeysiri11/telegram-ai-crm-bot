# AI Legal Guide — Sprint 31.2

## Reuse Enterprise AI

Platform Builder Concierge + AI Team Center assign role labels (no forked orchestration):

| Role label | Task focus |
|------------|------------|
| AI Lawyer | Claim strategy |
| AI Legal Assistant | Hearing checklist |
| AI Document Generator | Demand letter / NDA |
| AI Research Assistant | Statute research |
| AI Customer Success | Client status update |
| AI Analytics | Owner KPI summary |

## Vertical AI probes (existing)

- `/api/legal-aa/v1/assistant` — intake Q&A
- `/api/legal-aa/v1/research` — statute research
- `/api/legal-aa/v1/opinion` — memo (`issue` required)
- `/api/legal-cm/v1/ai` — case summary / next actions
- `/api/legal-di/v1/drafting` — NL drafting (`prompt` required)

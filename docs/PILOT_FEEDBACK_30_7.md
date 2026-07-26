# Pilot Feedback System — Sprint 30.7

## Central path (no duplicates)

Web form (`/pilot`) → **POST `/api/enterprise-epr/v1/feedback`** → EOC → EPI.

Classification → **POST `/api/enterprise-ele/v1/feedback`**.  
Critical/High → **POST `/api/enterprise-obs/v1/incidents`**.

Client: `src/web/src/integrations/pilotFeedback.ts`

## Collected categories

User feedback · AI feedback · Errors · Warnings · Suggestions · UX issues · Missing features

## Traceability

Every item: `trace_id`, severity (Critical/High/Medium/Low), assigned **existing module**, ELE class, optional `incident_id`, local history `ewp_pilot_feedback_v1`.

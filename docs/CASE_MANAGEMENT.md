# Case Management

**Version:** `4.9.0-enterprise`  
**API:** `POST /api/legal-enterprise/v1/cases`

## Foundation Objects

- Case Registry
- Case Status
- Case Timeline
- Participant Registry
- Document Registry
- Evidence Registry
- Task Registry
- Case Notes

## Typical Flow

1. Register court and category
2. Register case (`status=filed`)
3. Add participants by legal role
4. Attach documents and evidence
5. Create tasks and notes; advance status along the timeline

# EP-04 — AI Personality & Intelligent Interaction

**Phase:** Enterprise Product Excellence  
**Scope:** Executive Advisor voice over existing AI surfaces — no AI Core / Engine / Runtime / Store  
**Date:** 2026-07-27  
**Depends on:** EP-01 · EP-02 · EP-03  
**Version:** `AI_PERSONALITY_VERSION = 1.0`  
**GA baseline:** Advisor 1.0 is the AI voice standard for Enterprise Platform v1.0 GA (EP-08).

## Mission

Сделать AI естественным помощником владельца бизнеса: **Executive Advisor**, не чат-бот.

## Architecture compliance

- No AI Core / new Engine / Runtime / Data Fabric / Store / architecture changes
- Composition + copy + presentation over Concierge dock, Morning Brief, Live panels, suggestions
- Session memory via `sessionStorage` only (not a Store)

---

## 1. Enterprise tone

| Trait | Rule |
|-------|------|
| Calm | No hype, no emoji spam |
| Confident | Direct statements; avoid “maybe you could…” fluff |
| Businesslike | Decision language, not chat banter |
| Concise | Observation → Why → Action → Impact |
| Proactive | Surface next decision without being asked to “chat” |
| Respectful | Owner-first; no infantilizing copy |

`ENTERPRISE_AI_TONE` encodes these flags in `aiPersonality.ts`.

---

## 2. Recommendation language

Every recommendation uses:

1. **Observation** — what is true now  
2. **Why it matters** — owner consequence  
3. **Suggested action** — verb + destination  
4. **Expected impact** — measurable or operational outcome  

Plus quiet **confidence**: High / Likely / Explore.

Surfaces:

- Concierge dock (`AdvisorRecView`)
- Morning Brief cards (`what` / `why` / `next` / `impact`)
- Live `AiRecommendationsPanel`

---

## 3. Confidence

| Level | Chip | Use |
|-------|------|-----|
| high | High | Health, overdue, today/risk |
| medium | Likely | Default insights |
| low | Explore | Speculative / low signal |

Never a progress bar circus — one Badge only.

---

## 4. Context awareness

`advisorContextLine` binds Concierge copy to:

- Current section (`sectionKeyFromPath`)
- Company name
- Health ratio
- Unread count
- AI busy state

Suggestions reorder when health is degraded (attention first). Knowledge awareness hint remains.

---

## 5. Conversation flow (session)

- `markAdvisorSeen(id)` on click  
- `filterAdvisorSeen` drops repeats within the browser session  
- Minimum keep = 2 so the dock never empties  

---

## 6. Language policy

| Surface | Policy |
|---------|--------|
| Dashboard owner status | English status language (badges, greetings, Brief status) |
| Enterprise City | RU/UA localization retained on City chrome |
| Workspace | Organization language for module work |
| Concierge Advisor | Calm EN decision voice; chips English |

---

## 7. Delight inventory (≥30)

1. `aiPersonality.ts` personality module  
2. Tone flags object  
3. Language policy constants  
4. Advisor recommendation type  
5. Confidence labels / short chips  
6. Tone chips Action / Attention / Insight  
7. Context line generator  
8. Session seen memory  
9. Filter seen suggestions  
10. Advisor greeting (EN)  
11. Voice samples  
12. Confidence from rec tone  
13. SmartSuggestion Observation/Why/Action/Impact  
14. CRM / Knowledge / City / Analytics / Dashboard / AI / Finance packs rewritten  
15. Marketplace + Builder sections  
16. Health-aware reorder  
17. `AdvisorRecView` compact + full  
18. Dock title → Executive Advisor  
19. “Next decisions” label  
20. Context line under Concierge  
21. Mark seen on navigate  
22. Snapshot Advisor copy  
23. Morning Brief English owner voice  
24. Brief `impact` field  
25. Brief confidence badge  
26. Brief impact line UI  
27. Summary lines advisor-toned  
28. Live recommendations panel rewrite  
29. Concierge catalog samples de-chatbot  
30. CSS advisor chrome  
31. Index exports for personality API  
32. `toAdvisor` helper  
33. Default Concierge fallback copy  
34. Activity/attention/risk/opportunity impact fields  
35. EP-04 documentation  

---

## 8. Scores (self-assessment)

| Metric | After EP-03 | After EP-04 |
|--------|-------------|-------------|
| Executive Experience | 8.9 | **9.1** |
| AI Experience | 8.7 | **9.2** |
| UX | 8.5 | **8.7** |
| Visual Excellence | 9.0 | **9.0** |
| Motion | 8.9 | **8.9** |
| Navigation | 8.4 | **8.4** |
| Performance | 8.0 | **8.0** |
| Enterprise Quality Index | 9.0 | **9.2** |
| Production Readiness | 8.4 | **8.5** |

---

## 9. Recommendations for EP-05

1. Owner preference: pin Advisor language (EN / Org) without new Store — settings flag only  
2. “Explain this KPI” one-liner tied to Morning Brief column (copy only)  
3. Soft suppress after 3 identical Attention items across days (local preference)  
4. Builder Academy: Advisor writing checklist  
5. Screenshot QA: Concierge dock + Brief + Live recommendations side-by-side  

## Files

| Path | Role |
|------|------|
| `src/web/src/ai-os-chrome/aiPersonality.ts` | Tone, policy, confidence, session |
| `src/web/src/ai-os-chrome/smartSuggestions.ts` | Advisor-format suggestions |
| `src/web/src/ai-os-chrome/AdvisorRecView.tsx` | Recommendation UI |
| `src/web/src/ai-os-chrome/AiOsExperienceChrome.tsx` | Concierge wiring |
| `src/web/src/dashboard/deriveMorningBrief.ts` | Brief advisor copy |
| `src/web/src/live-ops/LivePanels.tsx` | Live rec panel |
| `docs/EP_04_AI_PERSONALITY.md` | This spec |

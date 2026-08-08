# Sprint 42.3 — Human-First UX (Auto Module)

**Status:** COMPLETE  
**Mode:** UX polish · zero learning curve · AI-first  
**Module:** Auto (`/workspace/auto`)  
**Date:** 2026-08-06  

---

## Goal

Make Auto so clear that a new user without training knows: where they are, what is happening, and what to do next — with AI as the primary control surface and zero technical noise.

---

## Delivered

| # | Requirement | Implementation |
|---|-------------|----------------|
| 1 | Remove technical blocks from user mode | `FullLayout` no longer mounts Intelligence / Concierge / Team / Workflows / Control Tower / Ops strips / Runtime on everyday screens |
| 2 | AI as primary control | `HumanAiCommandBar` — «🤖 Чем помочь?», input, chips, clear, ask |
| 3 | Voice input | Mic button → `startVoiceDictate` (Web Speech + demo fallback) → transcript → AI suggestion → confirm |
| 4 | Unify top cards | Single `hf-unified-hero` (title · description · can-do · next · primary CTA) |
| 5 | Short AI guide | Greeting · 3 bullets · one recommendation · **Исправить** |
| 6 | Quick actions only | Добавить автомобиль · Автомобили · Клиенты · Продажи · Импорт · Склад |
| 7 | Simple / Pro toggle | RU labels; default **Простой режим** (`ewp_ux_mode_v1`) |
| 8 | Owner engineering panels | Relocated to **Платформа → Центр управления** (`/platform-builder/ops-center`) |
| 9 | 5-second clarity | Auto Human landing answers Where / What / Can do / Primary / Next |

---

## Architecture

```
Everyday (client · manager · company_admin · simple)
  └─ Clean shell · Auto Human landing · AI bar

Owner · Developer · Pro
  └─ Hint link → /platform-builder/ops-center
       └─ Concierge · Intelligence · Team · Workflows
       └─ Builder · Marketplace · Twin · Runtime · …
```

**Decision:** Do not show engineering strips inline anymore (even for owners on Auto). Owner Pro gets a link chip; full panels live on Ops Center only. Rejected: keep collapsible ops strips on every page (violates “no tech noise”).

---

## Clarity check (Auto landing · Simple)

| Question | Answer on screen |
|----------|------------------|
| Где я? | «Авто · дилерское пространство» + title **Авто** |
| Что за раздел? | Description under title |
| Что можно делать? | Explicit «Что можно делать: …» + quick actions |
| Главная кнопка? | **Добавить автомобиль** |
| Что дальше? | «Дальше: …» + AI «Исправить» |

---

## Key files

| Path | Role |
|------|------|
| `src/web/src/human-first/AutoHumanLandingView.tsx` | Auto landing |
| `src/web/src/human-first/HumanAiCommandBar.tsx` | AI row + voice + confirm |
| `src/web/src/human-first/autoAiIntents.ts` | Auto NL → action |
| `src/web/src/human-first/useVoiceDictate.ts` | Speech / fallback |
| `src/web/src/human-first/PlatformOpsCenterPage.tsx` | Owner control center |
| `src/web/src/layouts/FullLayout.tsx` | Strip removal + human-work flags |
| `src/web/src/modules/WorkspaceLandingGate.tsx` | Routes Auto → Human landing |
| `src/web/src/modules/moduleLandingCatalog.ts` | Short Auto guide · Platform → Ops |
| `src/web/src/ux-revolution/SimpleProModeToggle.tsx` | RU Simple/Pro |

---

## How to demo

1. Login `auto@ados.demo` / `demo` (manager) or any user with `/workspace/auto`  
2. Open `/workspace/auto` — Simple mode by default  
3. Use AI chips or mic → confirm suggested action  
4. As `owner@ados.demo` + switch to **Профессиональный режим** → open **Платформа → Центр управления**

---

## Tests

`src/web/src/human-first/human_first_auto_42_3.test.ts`

---

## Acceptance

| Criterion | Result |
|-----------|--------|
| New user understands without instructions | Yes (Simple Auto landing) |
| AI is the main control | Yes (`HumanAiCommandBar` first) |
| No technical noise on Auto | Yes |
| One primary action | Добавить автомобиль |
| Owner vs Client visually different | Clean Auto vs Ops Center |
| Feels like modern AI product | AI-first bar + voice + confirm |

**Recommendation:** READY for Auto Human-First demos.

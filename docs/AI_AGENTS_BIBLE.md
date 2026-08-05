# The AI Agents Bible

**Status:** the canonical, highest-level design authority for AI agents across the ADOS platform.
Documentation only — no source code should be modified as a result of reading this document. This
Bible consolidates every place agents appear — the backend capability stack, the Executive Advisor
voice, City building AI labels, and Production Center studio agent-assignment — into one coherent
agent story, replacing the need to reconstruct it from `ARCHITECTURE_MAP.md` §5, `08_AI_PERSONALITY.md`,
`ENTERPRISE_CITY_BIBLE.md` §7, and `AI_PRODUCTION_CENTER_BIBLE.md` §3 independently.

## 0. The one persona, and the many capabilities beneath it — stated once, applies everywhere

Two facts must never be confused, in this document or any future one:

1. **There is exactly one AI *persona* in this platform: the Executive Advisor** (`08_AI_
   PERSONALITY.md`). Calm, confident, concise, proactive, respectful — reachable from the Command
   Palette's AI mode, the fixed AI Dock, and (vision) voice input. Every surface that speaks to a user
   as "the AI" uses this one voice. There is no second AI character anywhere in this platform, and any
   future feature proposing one should be rejected on this rule alone.
2. **There are many AI *capabilities* underneath that one voice** — a real backend package stack
   (§1), plus per-surface agent roles (§2–§4) that do work but do not get their own personality. A
   Production Center studio's "assigned agent" and a City building's "aiAssistant" label (§3, §4) are
   capabilities the one Advisor persona fronts, not additional personas.

## 1. The backend agent stack (real packages, layered)

```
platform_memory  →  platform_orchestrator (+ platform_agents)  →  platform_workflow / platform_tools
                 →  platform_reasoning / platform_planning / platform_decision
                 →  platform_learning / platform_collaboration
```

Real, shipped Python packages (`ARCHITECTURE_MAP.md` §5, `MODULES.md` §5) — memory/context at the
base, orchestration and agent registration next, execution (workflow/tools) above that, cognition
(reasoning/planning/decision) above that, and feedback/consensus (learning/collaboration) at the top.
Two honest caveats this Bible restates because they matter for every future agent-related decision:

- **A second, unrelated memory stack exists** (`platform_ai/memory/`, alongside `platform_memory/`) —
  not a secret, tracked as `TECH_DEBT.md` TD-21, but real duplication a new feature must not add a
  third instance of.
- **A standalone TypeScript agent runtime exists with zero connection to this Python stack**
  (`src/kernel`'s `@ados/orchestrator`, `ARCHITECTURE_MAP.md` §15). If a future sprint ever proposes
  agent work that could live in either stack, that choice is a real architectural decision requiring
  its own ADR (`00_MASTER_PRODUCT_BIBLE.md` §4) — never a default assumption in either direction.

## 2. Agent roles in the Production Center (real UI, capability not yet real)

`PRODUCTION_CENTER.md` documents real, working agent-assignment UI on each of the 17 studio cards
(`AI_PRODUCTION_CENTER_BIBLE.md` §3). The assignment itself — which agent is attached to which studio —
is real, persisted state. **What the assigned agent actually does once generation providers exist is
still the vision design in `AI_PRODUCTION_STUDIO.md` §19–§20**, restated here as the canonical agent
roster for this surface:

| Agent | Role |
|---|---|
| Creative Brief Agent | Turns a request into a structured generation brief |
| Generation Orchestration Agent | Drives a pipeline run, handles retries/fallback providers |
| Brand Compliance Agent | Validates output against brand rules before human approval |
| Publishing Agent | Prepares platform-specific exports, executes only after approval |
| AI Director | Decomposes a high-level creative goal into a multi-step plan across the above agents, adapting `platform_planning`'s real dependency-aware planning machinery with creative-domain vocabulary (`AI_PRODUCTION_STUDIO.md` §20) |

**Hard rule, no exceptions, restated for the third time across this documentation set because it is
the platform's single most important agent-governance fact:** no agent in this roster may publish or
take an externally-visible action without passing through human approval (`AI_PRODUCTION_CENTER_
BIBLE.md` §4's real, structurally-enforced Approval pipeline stage).

## 3. Agents in Enterprise City (real labels, real backend stack, honest status)

`CITY_DISTRICTS.md` confirms every City building carries a real `aiAssistant` field — "label wired to
Concierge / Agents." This is a real, shipped piece of data on every building, not a vision item. What
it connects to is the real backend stack (§1) and the real Concierge/smart-suggestions system
(`08_AI_PERSONALITY.md`, `useCityLiveStatus.ts`'s real `aiActive` signal for AI Team/Concierge
buildings). The AI-dot overlay on any building currently being worked on
(`ENTERPRISE_CITY_BIBLE.md` §7) remains the correct visualization pattern — a status signal on the
building being worked on, never a moving character wandering the map, in 2D today and, per that
Bible's §6, only ever as a deliberate transit-marker exception in the still-vision 3D mode.

## 4. Agents in Navigation (real, narrow)

The Command Palette's AI mode (`ENTERPRISE_NAVIGATION.md` §5, §8) runs a real, working NLU intent
parser (`aiCommandCenter`) that resolves natural-language requests into navigation/command actions.
This is the smallest, most mature real "agent" in the platform today — narrow in scope (navigation
intent only) but genuinely functioning, unlike the Production Center's assigned-but-not-yet-acting
agents (§2). It is the concrete proof that the Executive Advisor persona (§0) can front a real backend
capability, which is the model every future agent surface should follow: ship the narrow real thing
before promising the broad vision thing.

## 5. Agent transparency — the one interaction rule every agent surface must follow

Restated from `WORKSPACE_INTERACTIONS.md` §24 and `02_PRODUCT_PHILOSOPHY.md` principle 6, because it
governs every row in every table above without exception: **an agent's action is always visible and
attributed.** A Brand Compliance Agent's flag on an approval card, a Creative Brief Agent's draft, a
City building's AI-dot — none of them ever silently mutate state a human can't see happened. This Bible
treats this as the one non-negotiable rule an implementer should check before shipping any new agent
capability, the same way `02_PRODUCT_PHILOSOPHY.md` treats "no silent bypass of governance" as its one
truly non-negotiable principle platform-wide.

## 6. Status summary — what's real vs. vision, in one table

| Surface | Real today | Vision |
|---|---|---|
| Executive Advisor voice/tone/reachability | Yes — Dock, Palette AI mode | Voice-input navigation (`ENTERPRISE_NAVIGATION.md` §19) |
| Backend agent package stack (§1) | Yes, as packages | Full maturity across all layers varies; some packages thinner than others (`MODULES.md` §5) |
| Command Palette AI-mode NLU (§4) | Yes, narrow and working | Broader natural-language platform control |
| City building `aiAssistant` labels, AI-dot (§3) | Yes, real data + real visual signal | 3D-mode agent transit markers (`ENTERPRISE_CITY_BIBLE.md` §7) |
| Production Center studio agent-assignment (§2) | Yes, real assignment UI | The assigned agent actually generating anything — blocked on `AI_PRODUCTION_CENTER_BIBLE.md` §9's provider gap |
| AI Director, Creative Brief/Compliance/Publishing Agents (§2) | No | Full vision, `AI_PRODUCTION_STUDIO.md` §19–§20 |
| Multi-user AI collaboration (co-reviewer pattern) | No | `WORKSPACE_INTERACTIONS.md` §24 |

## Related documents

`08_AI_PERSONALITY.md` (the Advisor voice/tone this Bible's §0 restates as the one persona rule),
`ARCHITECTURE_MAP.md` §5, `MODULES.md` §5, `DEPENDENCY_MAP.md` §5 (the real backend stack in §1),
`AI_PRODUCTION_CENTER_BIBLE.md` (§2's studio-agent detail), `ENTERPRISE_CITY_BIBLE.md` §7 (§3's City
integration), `ENTERPRISE_NAVIGATION.md` §5, §8, §20 (§4's Palette AI mode), `WORKSPACE_
INTERACTIONS.md` §24 (§5's transparency rule), `02_PRODUCT_PHILOSOPHY.md`, `TECH_DEBT.md` (TD-21, TD-33
— the two honest caveats in §1).

# 08 — AI Personality, Ecosystem & Agents

**Chapter of the Master Product Bible.** Covers three required Bible topics together because they are
one continuous idea in this platform: the **voice** AI speaks in (`docs/EP_04_AI_PERSONALITY.md`,
`ENTERPRISE_DESIGN_SYSTEM.md` §16), the **ecosystem** of AI capability layers underneath it
(`ARCHITECTURE_MAP.md` §5, `MODULES.md` §5), and the **agents** that act within it
(`AI_PRODUCTION_STUDIO.md` §19–§20). Full detail lives in those documents — this chapter explains how
they form one AI story, not three separate ones.

## The one persona: Executive Advisor

Mission, stated once in `docs/EP_04_AI_PERSONALITY.md` and never contradicted anywhere else in the
platform: make AI a natural helper to the business owner — an **Executive Advisor**, not a chatbot.

| Trait | Rule |
|---|---|
| Calm | No hype, no emoji spam |
| Confident | Direct statements, no hedging |
| Businesslike | Decision language, not chat banter |
| Concise | Observation → Why → Action → Impact, nothing longer |
| Proactive | Surfaces the next decision unasked |
| Respectful | Owner-first, never infantilizing |

**Confidence is always one badge** (High/Likely/Explore) — never a percentage, never a progress bar
(`docs/EP_04_AI_PERSONALITY.md` §3). This voice is reachable from exactly three converging doors — the
fixed AI Dock, the Command Palette's AI mode, and (designed) voice input — and all three must agree,
because there is only ever one Advisor (`ENTERPRISE_NAVIGATION.md` §20).

## The ecosystem beneath the voice

The Advisor's voice is the visible tip of a real, layered AI capability stack
(`ARCHITECTURE_MAP.md` §5, `DEPENDENCY_MAP.md` §5):

```
platform_memory  →  platform_orchestrator (+ platform_agents)  →  platform_workflow/platform_tools
                 →  platform_reasoning / platform_planning / platform_decision
                 →  platform_learning / platform_collaboration
```

Two honest facts about this stack worth stating in the Bible rather than only in the deep audit docs:
**a second, unrelated memory stack exists** (`platform_ai/memory/`, alongside `platform_memory/`,
`TECH_DEBT.md` TD-21) and **a standalone TypeScript agent runtime exists with no connection to this
Python stack** (`src/kernel`'s `@ados/orchestrator`, `ARCHITECTURE_MAP.md` §15 item 5). Neither is a
secret — both are tracked, both are explicitly *not* something a new feature should build a third
version of; a future AI capability extends the Python stack above, and if the TypeScript runtime's
relationship to it is ever resolved, that resolution is itself a Bible-worthy architectural decision
(`CLAUDE.md`'s "every architectural decision must be documented").

## Agents: who does the work

Specialist agents register into `platform_agents`/`platform_orchestrator` — never a parallel agent
system per feature. Two concrete agent rosters exist in the specs so far:

- **Command/navigation agents** — the AI mode's NLU intent parser (`aiCommandCenter`,
  `ENTERPRISE_NAVIGATION.md` §5) and `smartSuggestions`'s context-aware recommender.
- **Creative agents** (`AI_PRODUCTION_STUDIO.md` §19–§20) — Creative Brief Agent, Generation
  Orchestration Agent, Brand Compliance Agent, Publishing Agent, and the AI Director (a creative-domain
  adaptation of the real `platform_planning`/`CapabilityRouter` machinery).

**The rule that unifies every agent in this platform, regardless of roster:** no agent publishes, acts
externally, or bypasses a governance gate without human approval where one exists
(`02_PRODUCT_PHILOSOPHY.md` principle 6). An agent's *authority* is to plan, generate, and recommend —
never to unilaterally finalize anything with external consequence.

## AI collaboration as a workspace concept

`WORKSPACE_INTERACTIONS.md` §24 extends this same Advisor relationship into a collaboration model: AI
as a co-reviewer, appearing in the same visual slot a human co-reviewer's comment would occupy, always
visible and attributed — never silent write access. This is the concrete design answer to "how do
humans and AI agents share one workspace," and it is deliberately the same answer as "how does the
Advisor talk to you" — one relationship, applied to a new context, not a new relationship invented for
collaboration specifically.

## Status honesty

The Executive Advisor voice, its tone rules, its recommendation structure, and its reachability from
Dock + Palette are **real and shipped** (`docs/EP_04_AI_PERSONALITY.md`). The Python AI capability
stack (`platform_memory` through `platform_collaboration`) is **real** as a package layer, though its
internal maturity varies by package (`MODULES.md` §5). The Production Studio's Creative Agents and AI
Director, voice-input navigation, and AI-collaboration-as-co-reviewer are **vision** — designed, not
built.

## Related chapters

`05_AI_PRODUCTION.md` (the largest concrete home for Creative Agents and the AI Director),
`03_ENTERPRISE_OS.md` (the AI Advisor as one of the OS's core "apps"), `09_ARCHITECTURE.md` (the
package-level detail behind the ecosystem diagram above).

# 05 — AI Production Studio (Chapter Summary)

**Chapter of the Master Product Bible.** The complete specification is `AI_PRODUCTION_STUDIO.md` (28
sections) — this chapter is a connecting summary. Read the full document for module-level detail
(image, video, voice, avatar, 3D, UI generation, brand library, publishing, etc.).

## What it is, in one line

The creative center of the platform: every image, video, voice, avatar, 3D asset, presentation, and
marketing campaign the enterprise produces flows through one governed pipeline — from idea, through
generation and brand compliance and human approval, to real publication — with full lineage back to
the prompt and rules that produced it (`AI_PRODUCTION_STUDIO.md` §1).

## Why it's in the Bible as its own chapter

The Studio is the platform's largest area of genuinely new capability rather than extended existing
capability — its own §0 grounding table found that real image/video/voice/avatar/3D generation, a
brand kit, a creative prompt library, and binary media versioning are **absent from the codebase
today**. It earns a dedicated Bible chapter precisely because it is the area most likely to be built
by future sprints without full context of what already exists nearby (Content Factory, Cross-Posting,
the stubbed Marketing OS) — the risk of duplicated effort here is the highest of any system in this
platform.

## The one architectural decision that matters most

`CrossPostingEngineV1` already has a complete, real scheduling/status-machine/analytics data layer for
social publishing — its actual publish call and analytics collection are **simulated** (fake URLs, fake
engagement numbers). The Studio's Publishing Center (§26) is designed as *replacing that simulated
bottom half with real platform API clients*, not building a parallel publisher. This is the single
highest-leverage extension point in the entire specification, and the clearest instance of
`02_PRODUCT_PHILOSOPHY.md` principle 2 (extension over replacement) in this platform's newest work.

## The shape of the full specification

| Section range | Covers |
|---|---|
| §0 | What's real (Content Factory, Cross-Posting, stubbed Marketing OS, text-only AI providers) vs. genuinely new (all real generation, brand kit, media storage) |
| §1–§3 | Vision, principles, provider architecture (new `TaskType`s extending `platform_ai`) |
| §4–§11 | The eight generation modalities: Image, Video, Voice, Avatar, Motion Graphics, Presentations, 3D Assets, UI Generation |
| §12–§13 | Reels Generator and Social Content Studio — composition layers over the base modalities |
| §14–§18 | Brand Library, Prompt Library, Creative Knowledge Base, Asset Versioning, Style Presets |
| §19–§26 | Creative Agents, AI Director, Workflow Builder, Pipeline, Production Queue, Rendering Farm, Approval, Publishing Center |
| §27–§28 | The end-to-end user journey, and how it scales to enterprise-level multi-team workflow |

## The one governance rule that never bends

**No agent publishes without human approval** (`ai_never_publishes_alone`, adopted directly from the
existing but stubbed `platform_ai_marketing_os`) — every automation shape, every AI Director plan,
every scheduled campaign still produces an asset in `pending_review` state. This is the Studio's
concrete instance of `02_PRODUCT_PHILOSOPHY.md` principle 6, and it is the one rule this document
states has **no exception, ever** (§21).

## Status honesty

Content Factory (text-only) and Cross-Posting (simulated publish) are real, narrow, existing systems
this Studio extends. Everything else in the specification — every generation modality, the Brand
Library, both libraries (prompt and knowledge), Asset Versioning, Style Presets, the AI Director, and
real (non-simulated) publishing — is vision. `10_ROADMAP.md` treats this as the largest single body of
future work in the platform.

## Related chapters

`03_ENTERPRISE_OS.md` (the Studio runs as an application inside this OS), `04_ENTERPRISE_CITY.md`
(a candidate future City building), `08_AI_PERSONALITY.md` (the Studio's Creative Agents and AI Director
speak in the same Executive Advisor voice, never a separate creative-AI personality).

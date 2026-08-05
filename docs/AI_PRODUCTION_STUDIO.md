# AI Production Studio — Complete Enterprise Product Specification

**Status:** permanent product bible chapter. Documentation only — no implementation shipped by this
document, no source code should be modified as a result of reading it. This is the **creative center
of the platform**: every image, video, voice, avatar, 3D asset, UI mockup, presentation, marketing
campaign, and social post the enterprise produces flows through one governed system, from idea to
published output. Written to be built **by extending existing platform substrate** — every section
states what is reused, what is extended, and what is genuinely new.

## 0. What already exists vs. what this designs

Read this first — several existing modules use the *same words* as this spec while meaning something
different; confusing them would be a real defect.

| Concept | Exists today? | Where | Reality check |
|---|---|---|---|
| Text content generation | **Yes, narrow** | `services/pg_content_factory_engine.py` (`ContentFactoryEngineV1`) | Generates car-listing marketing **text only** (description, Telegram/Instagram/TikTok-script/Facebook-ad copy) via an LLM text call. Real version numbering per `(car_id, content_type)`. Tightly coupled to the auto-dealer `Car` entity. |
| Cross-platform publishing | **Modeled, but simulated** | `services/pg_cross_posting_engine.py` (`CrossPostingEngineV1`) | Complete scheduling/status-machine/dedup/analytics data layer for Telegram/Instagram/Facebook/TikTok — but the actual publish call and analytics collection **fabricate** URLs/IDs/engagement numbers instead of calling real platform APIs. Real state machine, fake bottom half. |
| Channel credentials | **Stubbed** | `services/pg_channel_integration_engine.py` (`ChannelIntegration`) | Stores a caller-supplied token string per channel; no real OAuth flow, no outbound HTTP client anywhere. |
| Marketing OS / Creative Studio | **Fully stubbed** | `platform_ai_marketing_os/` (`AIMarketingOSLibrary`) | `CreativeStudio.generate()` returns a fake artifact string, no real generation call. **`AIApprovalWorkflow` is real and working** (approve/edit/reject/schedule state machine) — reused directly (§25). Its principle `ai_never_publishes_alone` is adopted as a hard rule throughout. Brand field shape (logo/colors/fonts/tone/positioning/audience/forbidden-words/templates) already speced in `docs/AMO_BRAND_CREATIVE_CONTENT.md` — adopted as-is in §14. |
| Messaging gateway | **Yes, different concern** | `platform_communications_hub/` | Transactional/1:1 messaging (SMS/email/push/chat) — not social-content broadcast. Kept strictly separate from Publishing Center (§26), even where both touch "Telegram." |
| AI provider infrastructure | **Text-only today** | `platform_ai/` (`ProviderRegistry`, `ProviderManager`, `TaskType`) | Only LLM/chat providers registered; `TaskType` enum has no image/video/voice/3D output type. The registry itself is a generic, structurally-ready-to-extend key-value store. |
| Cost tracking | **Real, but token-only** | `platform_ai/cost_tracker.py` | Tracks `tokens_in/tokens_out/cost_usd` per request/provider/model. **No compute-time, GPU-hour, or frame-count dimension exists** — required new ground for Rendering Farm billing (§24). |
| Generic tool/agent execution framework | **Yes, real** | `platform_tools/` (`AgentToolBridge`, `ToolAuditLog`) | Real, working registration/execution/audit framework — the correct integration point for every new generation provider (§3), not a bespoke path. |
| Async job engine | **Yes, real, generic** | `platform_jobs/job_engine.py` | Real `JobEngine` with `JobType` (IMMEDIATE/DELAYED/SCHEDULED/RECURRING/CRON/BATCH/PIPELINE), `JobState` incl. dead-letter, priority field, and a real `WorkerInfo` worker pool (`start(workers=4)`). No render-farm-specific concepts (no GPU/compute-node allocation, no frame/duration-based scheduling) — the correct foundation for Production Queue (§23), not a reason to build a separate queue. |
| Capability routing / planning | **Yes, real, but purely technical** | `platform_orchestrator/capability_routing.py` (`CapabilityRouter`), `platform_planning/` (`PlanningEngineConfig`, `ExecutionPlan`) | Real goal→decomposed-plan→routed-steps machinery (dependency-aware, replanning-capable) — but entirely domain-agnostic (steps have `capability`/`tool_id`/abstract `estimated_cost`, no shots/scenes/style-continuity vocabulary). The correct mechanical foundation for AI Director (§20), needing creative-domain adaptation, not a rewrite. |
| UI generation | **Catalog/wizard only, not generative** | `applications/platform_builder/builder_engine.py`, `ai_builder/wizard.py` | `BuilderEngine.preview()`/`create()` explicitly return `"frame_only": True` — static catalog selection and form-state capture, zero LLM-driven layout/component synthesis. Real, working, but not generation — the UI Generator (§9) is genuinely new capability, though its *rendering target* (how a generated UI actually gets composed into a Platform Builder page) should reuse Platform Builder's existing asset/rendering pipeline rather than inventing a second one. |
| 3D / geometry generation | **Metadata bookkeeping only, no geometry** | `applications/drone_platform/engineering/cad.py` | Real CAD *file reference* registry (STEP/STL/OBJ formats, part library, assembly records) — every method operates on metadata/paths, not actual mesh/geometry data; `preview_3d()` returns a thumbnail *path*, not a rendered image. No mesh generation, no point-cloud processing, no rendering engine anywhere in the repo. Digital Twin (`platform_enterprise_digital_twin`, `platform_builder/digital_twin/`) is confirmed to be a **read-only data/status mirror**, explicitly `"executes_business_logic": False"` — not 3D geometry. The 3D Asset Generator (§10) is genuinely new ground. |
| Style presets | **Absent beyond 3 themes** | `src/web/design-system/theme/index.ts` | Only `light/dark/corporate/custom` + a single `BrandOverrides` object exists — no preset gallery/template registry of any kind. Style Presets (§18) is genuinely new. |
| "Prompt library" | **Yes, different concept** | AI Builder Studio (`docs/AI_BUILDER_STUDIO_32_8.md`) | A library of prompts for constructing AI *agents* (system/user/corporate/favorite) — not creative-generation prompts. This spec's Prompt Library (§15) is distinct new ground; name collision only. |
| Brand kit, media asset storage/versioning, Creative Knowledge Base, real image/video/voice/avatar/3D generation, real YouTube/LinkedIn publishing | **No** | — | Zero matches repo-wide for any of these. Genuinely new (§§4–13, §16–17, §26). |

**Consequence for this design:** one new capability library plus one new application, following the
exact structural convention every other vertical in this repo already uses:

```
platform_production_studio/          # new capability library (mirrors platform_ai_marketing_os's shape)
applications/ai_production_studio/    # new application — API prefix /api/production-studio/v1
src/web/production-studio/            # new frontend feature area (sibling package, like platform-builder/)
```

---

## 1. Vision

The AI Production Studio is where an enterprise's ideas become finished, published creative work —
without a human ever hand-carrying an asset between five different tools. One brief becomes one
tracked pipeline (§22) that ends in an approved, published post, video, deck, or 3D asset, with full
lineage back to the prompt, brand rules, and consent records that produced it. It is designed the way
a film studio's production pipeline is designed — brief, generate, review, approve, publish, measure —
not the way a single "AI image tool" is designed.

## 2. Principles (carried through every module below)

1. **No agent publishes without human approval** (`ai_never_publishes_alone`, §0, §25) — no exceptions,
   ever, for any modality.
2. **Every asset is versioned and traceable** — from published post back to source prompt, brand-kit
   version, and consent record (§17).
3. **Reuse the provider, tool, job, and approval substrate that already exists** (§0) — never build a
   parallel engine for something the platform already has a generic version of.
4. **Format is chosen at generation time, not fixed at publish time** — an asset destined for TikTok is
   generated 9:16 from the start, never generated format-agnostic and cropped after (§26).
5. **Consent and rights are first-class generation metadata**, not a policy note to remember manually
   (§7, §8).
6. **Vendor-neutral by design** — this spec never names a specific generation vendor; provider choice is
   a build-time decision behind the provider registry (§3), not an architecture decision.

---

## 3. Provider architecture — extending `platform_ai`

New `TaskType` values, added alongside the existing text-only set:

```
IMAGE_GENERATION, IMAGE_EDIT, VIDEO_GENERATION, VOICE_SYNTHESIS, VOICE_CLONE,
AVATAR_GENERATION, ANIMATION_GENERATION, AUDIO_MIX, PRESENTATION_GENERATION,
ASSET_3D_GENERATION, UI_GENERATION
```

Each is a provider category in the existing `ProviderRegistry`/`ProviderManager` — a generation request
flows through `provider_manager.route(task_type, payload)` exactly as a chat completion does today.
`ModelCapabilities` gains matching boolean fields. **Every provider registers through
`platform_tools.AgentToolBridge`** (§0) so cost, latency, and success/failure are captured in
`ToolAuditLog` from day one. Cost tracking extends `platform_ai.cost_tracker` with a `unit_type`
dimension (token / image / second-of-video / second-of-audio / GPU-minute / frame) — generation APIs
bill by wildly different units than token-based LLM calls, and the existing tracker has no such field
(§0).

---

## 4. Image Production

- **Inputs:** prompt (free text or from the Prompt Library, §15), optional Brand Library binding (§14
  — auto-injects colors/tone/forbidden-words), optional reference image (style-transfer/edit —
  `IMAGE_EDIT`), and a target **format profile** (§26 — chosen at generation time, principle 4).
- **Output:** one or more candidate images written to Asset Versioning (§17) as new versions — never a
  bare file handed back uncatalogued.
- **Governance:** every call passes Brand Compliance validation (§14) and defaults `requires_approval:
  true` unless explicitly marked internal-draft-only.
- **Reuse:** the existing Pillow-based `marketing_media_processor.py` post-processing (resize/watermark)
  runs as the **last stage** after generation — not reimplemented.

## 5. Video Production

- **Inputs:** script/storyboard, duration target, format profile, optionally a linked Avatar (§7) or
  cloned Voice (§6).
- **Output:** a video asset **plus** a structured storyboard record (ordered scene list with per-scene
  prompt/duration/asset references) — so a single scene can be regenerated later without re-rendering
  the whole video.
- **Governance:** highest-cost, highest-risk modality — always `requires_approval: true`, no override.
  Runs through the Production Queue (§23) as a long-running job, never a synchronous call.

## 6. Voice Studio

- **Two modes:** **Voice synthesis** (`VOICE_SYNTHESIS` — a library voice reads a script) and **Voice
  cloning** (`VOICE_CLONE` — a new voice model trained from a reference sample of a real person).
- **Voice cloning requires a recorded `likeness_consent` reference at training time** — a hard
  validation gate, not a policy reminder — and that consent record travels with every asset later
  generated using that voice model.
- **A voice model is itself a versioned asset** (§17), distinct from any audio generated with it —
  retraining creates a new model version; past outputs record which version they used, staying
  reproducible even after the model changes.
- **Cost governance:** cloning (rare/expensive/one-time) and synthesis (frequent/cheap/per-use) are
  separate task types specifically so cost tracking and rate limits tune independently.

## 7. Avatar Studio

- **Two distinct avatar concepts:**
  1. **Static/branded avatar** — a generated character image (mascot, profile art) — Image Production
     (§4) with an `avatar` output tag, nothing more.
  2. **Presenter avatar** — a digital talking-head bound to a Voice (§6), narrating scripted Video
     content (§5). Genuinely new: an `AVATAR_GENERATION` provider taking (likeness reference *or*
     synthetic template + voice track + script) → a talking-head video segment.
- **Consent is a hard gate identical to Voice Cloning's** (§6) — an avatar bound to a real person's
  likeness without a recorded consent reference fails validation at generation time.
- Avatar assets live in the same Asset Versioning system as every other media type (§17) — not a
  separate subsystem, just a media type with extra required metadata.

## 8. Motion Graphics

- Treated as a **specialization of Video Production (§5)**, not a separate provider architecture: a
  motion-graphics/animated-explainer/animated-logo request is a video-generation request whose source
  has no live-action/avatar component.
- Reuses the storyboard-record pattern from §5 exactly — scenes without a bound Avatar/Voice, or with a
  fully synthetic (non-likeness) character reference, which sidesteps §7's consent gate since no real
  person's likeness is involved.

## 9. Enterprise Presentation Builder

- **Inputs:** outline or source document (can originate from `document_pdf_exporter.py`'s existing
  text-to-PDF pipeline in reverse), Brand Library binding (§14, for template/theme/color), target
  format (deck for live use, or a rendered video walkthrough chaining into §5).
- **Output:** a structured slide-deck asset (ordered slide records — layout, generated
  text/image/chart-reference per slide) plus an optional static export (PDF, via the existing
  exporter, reused directly) or video export (§5).
- **Distinct from Platform Builder's rendering engines** (`applications/platform_builder/rendering/`,
  `experience/`) — those render the no-code builder's own UI canvas (§0); presentation generation
  shares no code path with them despite overlapping "slide"/"layout" vocabulary.

## 10. 3D Asset Generator

**Genuinely new ground (§0) — no existing geometry generation, storage, or rendering capability
anywhere in the repo.** Designed scope:

- **Inputs:** a text/reference-image prompt describing an object, plus a target use (marketing render,
  product visualization, Platform Builder scene asset — see §0's UI Generator crossover note) and an
  output format (glTF/OBJ/STL, chosen for the consuming surface, not invented per request).
- **Output:** a 3D asset (mesh + materials) stored in Asset Versioning (§17) with the same
  content-addressed checksum/version-history model as every other media type — a 3D asset is not a
  second storage system, it is one more asset type.
- **Reuse boundary:** `applications/drone_platform/engineering/cad.py`'s `PART_LIBRARY`/format registry
  is a metadata-reference pattern worth reusing for cataloguing *engineering* CAD parts specifically —
  but it does not generate or render geometry, so it is a sibling reference point, not a dependency, for
  the Studio's 3D Asset Generator.
- **Rendering cost is compute-time/GPU-bound**, not token-bound — this is exactly what the extended
  `cost_tracker` unit-type dimension exists for (§3).

## 11. UI Generator

**Genuinely new ground (§0) — Platform Builder's own builder engine is explicitly catalog/frame-only
today, not generative.** Designed scope:

- **Inputs:** a natural-language description of a screen/component ("a dashboard card showing this
  quarter's top 5 leads") plus a Brand Library / Design System binding — **every UI Generator output
  must be constrained to `ENTERPRISE_DESIGN_SYSTEM.md`'s tokens** (colors, typography, spacing, card
  anatomy) so generated UI is never off-canon; this is a harder constraint than any other modality in
  this spec, because the output is itself product UI, not marketing content.
- **Output:** a structured UI specification (component tree + token bindings), not a raw image — this
  is what lets generated UI actually render as a real, functioning interface rather than a picture of
  one.
- **Consumption path:** a generated UI spec is designed to feed into Platform Builder's existing
  rendering/asset pipeline (`applications/platform_builder/rendering/`, §0) as its **input**, replacing
  today's catalog-selection step with an AI-generated one for tenants who opt in — this is the one
  place in this document where the Studio's output is meant to be consumed by another system's
  rendering engine rather than exported/published directly; it does not change Platform Builder's own
  "no business logic in rendering" rule (§0).
- **Approval applies here too** (§25) — generated UI is reviewed before it becomes available to
  end-users of the app it's built for, exactly like any other generated asset.

---

## 12. Reels Generator

A **specialized product surface**, not a new provider category: short-form vertical video (TikTok,
Instagram Reels, YouTube Shorts) has distinct constraints — strict 9:16, 15–60s duration bands,
caption/hook conventions, trending-audio conventions — that deserve a dedicated composer rather than
making every user re-derive them from the generic Video Production flow (§5) each time.

- **Composes**, rather than generates from scratch: Video Production (§5) for the base clip, Voice
  Studio (§6) for narration/voiceover, and Brand Library (§14) for consistent intro/outro branding —
  the Reels Generator is an opinionated template layer over §5, §6, §14, not a fifth generation
  provider.
- **Format profile is locked to vertical short-form by default** (§26 principle) — a user does not
  need to manually configure aspect ratio/duration for this surface; that's the point of it existing.
- **Publishing target is pre-selected to the short-form-native platforms** (§26: TikTok, Instagram
  Reels, YouTube Shorts) — publishing to a non-short-form destination from this surface is possible but
  requires an explicit override, since it's not the surface's design center.

## 13. Social Content Studio

The **composition layer above individual generation modules** — where a single business idea ("promote
this new listing") becomes a coordinated **set** of platform-specific assets, not one asset reused
everywhere:

- Takes one Creative Brief (§20's Creative Brief Agent) and fans it out into per-platform variants —
  an Instagram carousel, a TikTok Reel (via §12), a LinkedIn text+image post, a Facebook ad — each
  generated with its own format profile (§26) and, where tone should differ (LinkedIn vs. TikTok, per
  `ENTERPRISE_DESIGN_SYSTEM.md`-style tone differentiation), its own Brand Library tone-of-voice
  application (§14).
- **This is the surface a marketer actually opens day-to-day** — Image/Video/Voice/Avatar/Reels
  Production (§4–§8, §12) are the underlying capabilities; Social Content Studio is the workspace that
  orchestrates them into one campaign moment across channels.
- Every asset it produces still individually passes through Approval (§25) before its own
  platform-specific publish (§26) — the Studio composes the *plan*, it never bypasses per-asset
  governance.

## 14. Brand Library

Adopts the field shape already specified in `docs/AMO_BRAND_CREATIVE_CONTENT.md`'s `BrandCenter`
intent (§0), implemented for real, and generalized to a **library** (multiple brand profiles per
tenant, not one):

| Field | Purpose |
|---|---|
| Logo (+ light/dark/mono variants) | Injected into image/video/presentation/3D-render generation as a required visual element when brand-bound |
| Color palette | Injected as generation constraints across every modality |
| Typography | Injected into presentation and text-overlay generation |
| Tone of voice | Injected into every text-prompt-driven generation as an explicit style constraint |
| Positioning / audience | Context injected into prompt construction |
| Approved / forbidden words | **Hard validation** — generated text containing a forbidden word fails before reaching the approval queue |
| Templates | Reusable structural presets (per-platform image templates, presentation themes, Reels intro/outro) |

**One or more brand profiles per tenant**, scoped per sub-brand/vertical (a multi-vertical tenant
running both Auto and Agro storefronts may need two identities) — mirrors the platform's existing
per-tenant/per-vertical scoping (`platform_management`), not a new multi-tenancy mechanism.

## 15. Prompt Library

Distinct from AI Builder Studio's agent-construction prompt library (§0) — this one stores **creative
generation** prompts:

- **Structure:** prompt template with variable slots (e.g. `{product}`, `{audience}`, `{brand_tone}`
  auto-filled from the Brand Library, §14), target modality, and usage/performance metadata (linked
  back from Publishing analytics once real, §26).
- **Organization:** system (platform-provided starting templates per modality/vertical), organization
  (tenant-authored, shared), and favorites (per-user) — the same three-tier shape AI Builder Studio's
  prompt library already uses, reused for mental-model consistency even though the content is unrelated.
- **Storage substrate:** text-and-metadata only — built on `platform_memory`'s **pattern** (semantic
  search over prompt text via embeddings), not the Asset Versioning system (§17), which is for binary
  output. Conflating prompts (knowledge) with generated media (binary output) into one storage system
  would be a real design mistake.

## 16. Creative Knowledge Base

**Distinct from the Prompt Library** — where Prompt Library stores *what to ask for*, the Creative
Knowledge Base stores *what was learned from what happened*:

- **Content:** creative briefs and their outcomes (which prompt/brand-binding/format produced which
  published asset), performance summaries once real Publishing analytics exist (§26), style notes from
  edit-requested Approval feedback (§25), and platform-specific learnings (e.g. "LinkedIn posts with a
  question in the first line outperform statements for this tenant").
- **Consumption:** the Creative Brief Agent (§20) and AI Director (§20) query this base when drafting a
  new brief, so recommendations improve from the tenant's own history rather than starting cold each
  time — this is the feedback loop that makes the Studio a genuinely learning system rather than a
  one-shot generator.
- **Storage substrate:** built on the same `platform_memory` semantic-search pattern as the Prompt
  Library (§15) — knowledge and prompts can share the underlying mechanism even though they are
  conceptually distinct libraries with distinct content types.

## 17. Asset Versioning

Genuinely new — nothing in the repo stores or versions binary creative media today (§0). Reuses the
**pattern**, not the code, of Platform Builder's `VersionRegistry` (record/history/rollback +
checksum-based dedup, §0), which currently versions UI-canvas assets only:

- **Content-addressed by checksum**, deduplicating identical regenerated outputs.
- **Immutable version history** — regenerating/editing creates a new version, never overwrites; a
  video's storyboard record (§5) references specific scene-asset *versions*, keeping lineage
  reconstructable even after component assets are later regenerated.
- **Rollback is first-class**, mirroring the Builder pattern — reverting doesn't delete the newer
  version, it changes which version is "current."
- **Asset relationships form a lineage graph:** generated-from (prompt → asset), composed-of (Reel →
  clip + voice track + brand intro), derived-from (published crop → source image), consent-bound-to
  (avatar/voice → consent record, §6/§7). This lineage graph is what makes the Studio auditable
  end-to-end.
- **Applies uniformly to every asset type in this document** — image, video, voice model, audio, 3D
  mesh, UI spec, presentation, avatar — one system, not one per modality.

## 18. Style Presets

**Genuinely new — only a 3-theme + custom-override system exists today** (§0). Designed as a preset
**gallery** layered on top of, not replacing, the existing theme engine:

- A style preset bundles a coherent set of generation constraints — palette, typography pairing, image
  mood/lighting descriptors, video pacing/transition style, 3D render lighting setup — reusable across
  every modality in one selection, rather than a user manually tuning each generation's style
  independently every time.
- **Presets are Brand-Library-aware**, not a competing concept: a tenant's Brand Library (§14) can pin a
  default preset, and individual generations can override it per-asset.
- **System presets** (platform-provided starting points per industry/vertical) and **organization
  presets** (tenant-saved combinations) — the same system/organization/favorite three-tier pattern used
  by the Prompt Library (§15), for the same mental-model-consistency reason.

---

## 19. Creative Agents

Specialist agents registered in the existing agent stack (`platform_agents`/`platform_orchestrator`,
§0) — not a parallel agent system:

| Agent | Role |
|---|---|
| Creative Brief Agent | Turns a short human request into a structured generation brief — modality, format profile, Brand Library binding, Prompt Library template, informed by the Creative Knowledge Base (§16) |
| Generation Orchestration Agent | Drives a Pipeline (§22) — invokes providers via `AgentToolBridge` (§3), handles retries/fallback providers, assembles multi-asset compositions |
| Brand Compliance Agent | Validates generated output against Brand Library constraints (§14) before it reaches Approval (§25) |
| Publishing Agent | Prepares platform-specific export variants (§26) and schedules/executes publish jobs once approved, never before |

**Hard rule, no exceptions:** no Creative Agent may publish without passing through Approval (§25),
even automated pipeline runs (§21's automation shapes) — automation controls *when* generation happens,
never *whether* a human reviews before publish.

## 20. AI Director

The **top-level creative-orchestration role** — grounded in `platform_orchestrator.CapabilityRouter`
and `platform_planning`'s real goal→plan→routed-steps machinery (§0), adapted with creative-domain
vocabulary that doesn't exist in those modules today:

- **Takes a high-level creative goal** ("launch campaign for the new SUV listing across Instagram and
  TikTok") and decomposes it into a plan whose steps are creative concepts — shots, scenes, brand
  touchpoints, per-platform variants — rather than the generic `capability`/`tool_id` steps
  `platform_planning` produces natively today.
- **Delegates each step to the right Creative Agent** (§19) via the same dependency-aware/replanning
  planning strategies `platform_planning` already implements (SEQUENTIAL, PARALLEL, HIERARCHICAL,
  DEPENDENCY_AWARE, ADAPTIVE_REPLANNING) — reused mechanically, extended with a creative step-type
  vocabulary layered on top.
- **Owns style continuity across a multi-asset production** — e.g. ensuring every scene in a Video
  Production job (§5) and every platform variant in a Social Content Studio fan-out (§13) shares one
  Style Preset (§18) and Brand Library binding (§14), rather than each generation stage independently
  re-deriving style.
- **Does not bypass Approval** (§25) — the AI Director's plan produces assets that still individually
  enter the approval queue; "director" describes creative orchestration authority, not publishing
  authority.

## 21. Workflow Builder

**Distinct from the Pipeline (§22)** — the Workflow Builder is the user-facing visual composer;
the Pipeline is what actually executes. A marketer or creative lead builds/edits a workflow (which
stages run, in what order, with which approval gates and publish targets) without touching the
underlying `platform_workflows` definition directly — the same "no-code composition over an existing
engine" relationship Platform Builder already has with its own rendering system (§0).

- **Reuses `platform_workflows`/`platform_workflow`** as the actual execution engine (per `CLAUDE.md`'s
  reuse-first principle) — the Workflow Builder produces a workflow *definition*, it does not implement
  a second workflow runtime.
- **Three sanctioned automation shapes**, matching the platform's existing automation vocabulary (§0):
  scheduled campaigns (a Prompt Library template + Brand Library binding + publish-channel set +
  cadence), event-triggered generation (a marketplace/business event from `PlatformEventBus` triggers a
  Creative Brief Agent draft), and template-driven bulk generation (one template applied across many
  source items, e.g. a branded image for every active listing).
- **Automation never bypasses Approval** (§25) — this is restated here deliberately, because a
  Workflow Builder is exactly the kind of surface where a well-meaning "auto-approve after N hours"
  feature request will eventually arrive; the answer is no, by design, permanently.

## 22. Pipeline (execution) & Animation Pipeline

A **pipeline** is an ordered sequence of generation/transformation/validation/publish stages — the
Workflow Builder's (§21) execution counterpart, implemented as a `platform_workflows` definition:

```
Brief → Generate (§§4–12) → Brand Compliance check (§19) → Asset Versioning write (§17)
      → Approval (§25) → Publishing Agent (§19) → Publishing Center (§26) → real platform API
      → Analytics collection → Creative Knowledge Base feedback (§16)
```

- **Every stage is independently retryable and independently audited** via `ToolAuditLog` (§3).
- **Long-running stages run as async Production Queue jobs** (§23), never blocking requests.
- **A pipeline is resumable, not atomic** — a partially-complete multi-asset composition (a podcast-
  style multi-segment production, a multi-scene video) keeps its completed sub-assets in Asset
  Versioning (§17) and resumes from the failed stage.

**Animation Pipeline** is this same execution model applied specifically to any animation-bearing
asset (Motion Graphics §8, Video Production §5 with animated segments, avatar-narrated video §7) — it
is not a sixth separate pipeline type, it is the general Pipeline with animation-specific stages
(scene assembly → frame render → compositing → export) filled in.

## 23. Production Queue

Built directly on the real, existing `platform_jobs.JobEngine` (§0) — `JobType.PIPELINE`/`BATCH` for
multi-stage creative jobs, `JobState` (including `DEAD_LETTER` for permanently-failed renders), the
existing `priority` field for queue ordering, and the existing `WorkerInfo` worker-pool concept for
concurrency control. **This is an extension of the existing job engine, not a new queue system** — the
Studio's addition is domain-specific job payloads (generation briefs, storyboards, render specs), not
new queue mechanics.

## 24. Rendering Farm

The **compute-heavy execution layer** for Video Production (§5), Motion Graphics (§8), 3D Asset
Generation (§10), and Animation Pipeline (§22) rendering stages specifically — an extension of the
Production Queue (§23) with two things the generic job engine doesn't have today (§0):

1. **Compute-resource-aware scheduling** — a render job requests a resource class (CPU-only,
   GPU-accelerated, GPU-tier) rather than just a priority number; the worker-pool concept in
   `JobEngine` extends to distinguish worker *types*, not just worker *count*.
2. **Time/resource-based cost tracking** — using the extended `cost_tracker` unit-type dimension (§3):
   GPU-minutes or per-frame cost, tracked per job, rolled up per tenant/campaign the same way token
   cost rolls up for LLM calls today.

**The Rendering Farm is not a new infrastructure product** — it is the specific configuration of the
Production Queue for compute-heavy creative jobs; a tenant never interacts with "the Rendering Farm"
directly, they submit a Video Production or 3D Asset job and the Queue routes it to farm-class workers
automatically based on job type.

## 25. Approval Workflow

Built directly on **`platform_ai_marketing_os`'s existing `AIApprovalWorkflow`** (§0) — a real,
working state machine (create card → approve / edit / reject / schedule) — extended, not replaced, to
cover every module in this document:

- **One approval card per generated or composed asset** (one card for an assembled Reel, not one per
  clip/voice-track component).
- **Card states:** `pending_review → approved | rejected | edit_requested`, plus `scheduled` and
  `published` (terminal, cross-referenced to the Publishing Center job that executed it).
- **Edit-requested loops back to Generation** with specific feedback, which becomes Creative Knowledge
  Base metadata (§16) on what didn't work — never a blank-slate restart.
- **Reviewer role governed by existing RBAC** (`platform_identity`/`platform_management`) — no new
  permission system.
- **No expiry-based auto-approval, ever.** An asset in `pending_review` stays unpublished indefinitely;
  there is no timeout that promotes a card to `approved` on its own.

## 26. Publishing Center

Extends `CrossPostingEngineV1`'s real state machine (§0) with real platform API clients behind it —
replacing the simulated bottom half, not rebuilding the top:

| Platform | Content types | Design notes |
|---|---|---|
| **TikTok** | Reels-format short video (§12) | Vertical 9:16 mandatory at generation time; existing `PostingChannelType.TIKTOK` reused |
| **Instagram** | Image, carousel, Reels, Stories | Format profile carries a *placement* dimension (feed/Reels/Stories), not just aspect ratio; existing `PostingChannelType.INSTAGRAM` reused |
| **YouTube** | Long-form video (§5) and Shorts (§12) | **New channel type**; needs its own OAuth/resumable-upload credential flow behind `ChannelIntegration` — real new integration work |
| **Facebook** | Image, video, link posts (Pages) | Existing `PostingChannelType.FACEBOOK` reused; can share one Meta OAuth flow with Instagram underneath two channel values |
| **LinkedIn** | Image, video, article/text posts (Organization Pages) | **New channel type**; distinct tone handled entirely by Brand Library tone-of-voice (§14) + per-channel Prompt Library templates (§15), not special-cased publishing code |
| **Telegram** | Image, video, audio, presentation-export document | Reuses existing `PostingChannelType.TELEGRAM` and `IntegrationChannelType.TELEGRAM_CHANNEL`/`TELEGRAM_GROUP` — kept clearly separate from `platform_communications_hub`'s transactional Telegram channel (§0) |

**Design rules:** format chosen at generation time (§26, principle 4); real OAuth2 credentials replace
the `token_reference` stub; analytics become real and feed the Creative Knowledge Base (§16); every
publish requires an `approved`/`scheduled` asset, enforced at the engine layer, not just the UI; rate
limits and platform policy are per-channel configuration, treated as a hard stop with backoff, never
retried to force success.

---

## 27. From idea to final export — the user journey

A single walk-through tying every module above into one path:

1. **Idea.** A user types a request into the Creative Brief Agent (§19) or the Social Content Studio
   (§13): "promote our new SUV listing on Instagram and TikTok."
2. **Brief.** The Creative Brief Agent consults the Creative Knowledge Base (§16) for what's worked
   before, selects a Prompt Library template (§15) and Style Preset (§18), and binds the tenant's
   Brand Library (§14).
3. **Plan.** For anything beyond a single asset, the AI Director (§20) decomposes the brief into a
   multi-step plan — e.g. one Reel (§12) for TikTok, one carousel (Image Production, §4) for Instagram
   — assigning each step to the right Creative Agent (§19).
4. **Generate.** Each step runs as a Production Queue job (§23), using Rendering Farm resources (§24)
   for the video step; every output lands in Asset Versioning (§17) as a new, checksummed version with
   full lineage back to the brief.
5. **Comply.** The Brand Compliance Agent (§19) validates every generated asset against the Brand
   Library before it can reach a human.
6. **Review.** Each asset appears as an Approval card (§25). A reviewer approves, requests an edit
   (looping back to step 4 with specific feedback), or rejects.
7. **Schedule/Publish.** Approved assets move to `scheduled`, and the Publishing Agent (§19) executes
   the real platform-specific publish through the Publishing Center (§26) at the scheduled time.
8. **Measure & learn.** Real analytics (§26) feed back into the Creative Knowledge Base (§16), so the
   next brief on a similar topic starts smarter than this one did.

No step in this journey requires a human to manually move a file between tools — the pipeline (§22)
carries the asset and its lineage through every stage automatically; humans only touch the Brief and
the Approval steps.

## 28. Enterprise-level workflow

At enterprise scale, the same journey (§27) gains governance layers that a single-user flow doesn't
need:

- **Multi-team briefs.** A brief can originate from Marketing, get its avatar/voice component from a
  Communications team's approved presenter library (§7/§6), and its Brand Library binding locked to a
  corporate (not team-level) profile (§14) — the Studio supports multiple contributing teams on one
  pipeline without each team needing edit rights to every stage.
- **Tiered approval.** A single Approval card (§25) can require sign-off from more than one reviewer
  role for enterprise-sensitive content (e.g. legal review for regulated-industry claims, brand review
  for anything using a cloned executive voice/avatar, §6/§7) — modeled as multiple required approvals
  on one card, not multiple separate cards, so the asset's status stays singular and auditable.
- **Campaign-level rollups.** The Social Content Studio (§13) and Workflow Builder's scheduled-campaign
  automation (§21) operate at the campaign level, not just the single-asset level — an enterprise
  marketing lead sees one campaign's full multi-platform, multi-team pipeline status, not fifteen
  independent asset cards to mentally reassemble.
- **Cost governance at scale.** Rendering Farm and provider costs (§3, §24) roll up per campaign, per
  team, and per tenant — an enterprise finance/ops stakeholder can see creative production cost the
  same way they see any other operational cost line, using the same extended `cost_tracker` mechanism
  every other generation call reports through.
- **Everything above is additive to §27's single-user journey, never a separate system** — an
  enterprise user and a small-team user run through the exact same eight steps; enterprise scale adds
  more approvers and more rollup views, not a different pipeline.

---

## Related documents

- `CLAUDE.md` — "AI-first development," "reuse services before creating new ones," and "never break
  existing APIs" principles this design is built to satisfy.
- `ENTERPRISE_DESIGN_SYSTEM.md` — the visual/motion/AI-voice canon the Studio's frontend
  (`src/web/production-studio/`) must follow; the UI Generator (§11) has the hardest dependency on this
  document of any module here.
- `ENTERPRISE_CITY.md` — a candidate future City building (§9.2 there) if this system ships.
- `ENTERPRISE_NAVIGATION.md` — how the Studio's surfaces (Social Content Studio, Workflow Builder,
  Production Queue dashboard) register into the platform's global navigation and command palette.
- `WORKSPACE_INTERACTIONS.md` — the interaction patterns (drag/drop for storyboard reordering, approval
  card actions, notifications for job completion) the Studio's UI should follow.
- `docs/AMO_BRAND_CREATIVE_CONTENT.md`, `docs/ENTERPRISE_AI_MARKETING_OS.md` — the existing stubbed
  Marketing OS this spec extends into a real system.
- `MODULES.md`, `API_MAP.md` — catalog/endpoint conventions this design's new module and API prefix
  follow.
- `TECH_DEBT.md` — record the gap between `CrossPostingEngineV1`'s simulated publish/analytics
  functions and this design's "real API" requirement (§26) as a tracked item once implementation
  begins; it remains the single largest concrete gap this document identifies.

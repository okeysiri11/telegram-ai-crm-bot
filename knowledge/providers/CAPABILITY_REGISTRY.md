---
title: ADOS Capability Registry
aliases:
  - Capability Registry
tags:
  - providers
  - upp
  - capabilities
status: foundation
---

# ADOS Capability Registry

## Purpose

Describe the **catalog of capabilities**—stable verbs ADOS uses to request external work. Providers advertise which capabilities they implement; Router matches on these ids—not on vendor names.

UPP: [[UNIVERSAL_PROVIDER_PLATFORM]] · Router: [[PROVIDER_ROUTER]] · Interface: `capabilities()`

---

## Capability principles

1. **Stable ids** — lowercase snake or dotted (`image_generation`, `repository.clone`).  
2. **Vendor-neutral** — no `openai_chat`; use `chat`.  
3. **Additive** — new capabilities do not break old providers.  
4. **Documented params** — each capability has a normalized request schema.  
5. **Owned** — Knowledge/Infrastructure maintain the catalog; Core does not hardcode vendor lists.

---

## Core capabilities (examples)

| Capability | Intent |
|------------|--------|
| **chat** | Conversational / completion LLM |
| **vision** | Image understanding |
| **image_generation** | Generate images |
| **video_generation** | Generate video |
| **speech** | Text-to-speech |
| **speech_to_text** | Transcription |
| **embeddings** | Vector embeddings |
| **reasoning** | Extended reasoning / chain-of-thought style models |
| **translation** | Language translation |
| **search** | External web/enterprise search |
| **code_generation** | Code-focused generation (still via LLM providers) |
| **deployment** | Deploy artifacts / release actions |
| **repository** | VCS: clone, PR, commit, issues bridge |
| **storage** | Object/file storage |
| **knowledge** | External knowledge surfaces sync (e.g. wiki push/pull) |
| **calendar** | Calendar read/write |
| **payments** | Payment rails (PCI-aware; strict security) |
| **notifications** | Push/email/chat notifications |

---

## Messaging & collab (mapped)

Often implemented via **notifications** plus channel-specific providers (Telegram, Discord, Slack) that also expose narrow extras—prefer registering explicit capabilities (`notifications.send`) over brand verbs.

---

## Capability record (logical)

```text
Capability ID:     image_generation
Description:       …
Request schema:    { prompt, size, … }
Response schema:   { assets[], … }
Streaming:         yes | no
Security class:    standard | sensitive | regulated
Owners:            Infrastructure + Security (if regulated)
```

---

## Provider mapping examples

| Capability | Example providers |
|------------|-------------------|
| chat | OpenAI, Claude, Gemini, Ollama, LM Studio |
| repository | GitHub, GitLab |
| knowledge | Obsidian, Notion |
| notifications | Telegram, Discord, Slack |
| calendar | Google Calendar, Microsoft 365 |
| deployment | Docker, Kubernetes (+ CI providers) |
| storage | Google Drive, others |

Full list: [[SUPPORTED_PROVIDERS]].

---

## Evolution

- New capability → add to this registry + Normalization schemas → providers opt in.  
- **ADOS Core unchanged.**  
- Modules request the new capability only after Knowledge documents it.

---

## Related

[[NORMALIZATION_LAYER]] · [[PROVIDER_REGISTRY]] · [[PROVIDER_SECURITY]]

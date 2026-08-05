---
title: ADOS Supported Providers
aliases:
  - Supported Providers
tags:
  - providers
  - upp
  - catalog
status: foundation
---

# ADOS Supported Providers (Initial)

## Purpose

List the **initial providers** planned for UPP. Presence here means architectural intent—each still requires an adapter implementing [[PROVIDER_INTERFACE]], registry entry, and capabilities mapping.

UPP: [[UNIVERSAL_PROVIDER_PLATFORM]] · Capabilities: [[CAPABILITY_REGISTRY]]

---

## Initial providers

| Provider | Typical capabilities |
|----------|----------------------|
| **Cursor** | code_generation (host), chat (session bridge), repository (workspace) |
| **GitHub** | repository, deployment (Actions bridge), notifications (webhooks) |
| **OpenAI** | chat, vision, image_generation, speech, speech_to_text, embeddings, reasoning, code_generation |
| **Claude** | chat, vision, reasoning, code_generation |
| **Gemini** | chat, vision, embeddings, reasoning, code_generation |
| **Ollama** | chat, embeddings, code_generation (local) |
| **LM Studio** | chat, embeddings, code_generation (local) |
| **Obsidian** | knowledge |
| **Telegram** | notifications |
| **Discord** | notifications |
| **Slack** | notifications |
| **Notion** | knowledge, storage (pages) |
| **Google Drive** | storage |
| **Google Calendar** | calendar |
| **Microsoft 365** | calendar, storage, notifications (mail/teams as scoped) |
| **GitLab** | repository, deployment |
| **Jira** | (work-tracking via search/notifications-style issue ops—register explicit caps as added) |
| **Linear** | (same pattern as Jira) |
| **Docker** | deployment |
| **Kubernetes** | deployment |

---

## Grouping

| Class | Providers |
|-------|-----------|
| **IDE / host** | Cursor |
| **LLM cloud** | OpenAI, Claude, Gemini |
| **LLM local** | Ollama, LM Studio |
| **Knowledge** | Obsidian, Notion |
| **Messaging** | Telegram, Discord, Slack |
| **Productivity** | Google Drive, Google Calendar, Microsoft 365 |
| **VCS / DevOps** | GitHub, GitLab, Docker, Kubernetes |
| **Work tracking** | Jira, Linear |

---

## Add process (no Core change)

```text
1. Implement Provider Interface adapter
2. Map capabilities + normalization
3. Configure secrets (Provider Security)
4. Register Provider ID, Priority, Fallback
5. Validate via Provider Manager
6. Document in this list + Knowledge
```

ADOS Core and business modules remain untouched.

---

## Related

[[PROVIDER_REGISTRY]] · [[PROVIDER_ROUTER]] · [[FAILOVER_SYSTEM]] · [[../ados_os/MODULE_SYSTEM|MODULE_SYSTEM]]

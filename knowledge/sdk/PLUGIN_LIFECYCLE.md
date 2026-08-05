---
title: ADOS Plugin Lifecycle
aliases:
  - Plugin Lifecycle
tags:
  - sdk
  - plugins
  - lifecycle
status: foundation
---

# ADOS Plugin Lifecycle

## Purpose

Describe the **lifecycle stages** of a plugin from first install to removal, including health, enable/disable, and upgrade.

SDK: [[SDK_OVERVIEW]] · Manifest: [[PLUGIN_MANIFEST]] · Store: [[PLUGIN_STORE]]

---

## Lifecycle

```text
Install
    ↓
Register
    ↓
Initialize
    ↓
Health Check
    ↓
Enable
    ↓
(Disable ↔ Enable)
    ↓
Upgrade
    ↓
Unload
    ↓
Remove
```

---

## Stage definitions

### Install

- Artifact obtained (Store, partner channel, or internal package).  
- Signature and Compatibility verified when required.  
- Files placed in plugin area; **not** yet callable.

### Register

- Manifest parsed; Plugin ID + Version recorded.  
- Dependencies checked against Service/Plugin registries.  
- Permissions requested (not yet granted beyond install scope).

### Initialize

- Entry points loaded; SDK context injected.  
- Provider Plugins call adapter `initialize()` patterns.  
- Failure → remain disabled; Owner alerted.

### Health Check

- Plugin reports health (mirrors OS Service health).  
- Unhealthy plugins cannot Enable (or auto-Disable if already enabled).

### Enable

- Permissions activated per grant.  
- Hooks subscribed; services advertised to Runtime/OS.  
- Emit register/activate style events for agents/workflows as applicable.

### Disable

- Hooks unsubscribed; new Task routing stops using plugin.  
- In-flight work drained or cancelled per policy.  
- Config retained; easy re-Enable.

### Upgrade

- New Version installed alongside or replacing.  
- Compatibility + migration hooks.  
- Health Check → Enable new → Unload old.  
- Rollback if health fails.

### Unload

- Runtime releases code/resources; sessions using plugin end or migrate.  
- Registry Status → unloaded; artifact may remain on disk.

### Remove

- Artifact deleted; grants revoked; Knowledge/Store tombstone optional.  
- Irreversible without re-Install.

---

## State machine (summary)

| From | To |
|------|-----|
| Install | Register |
| Register | Initialize |
| Initialize | Health Check |
| Health Check | Enable \| (stay registered unhealthy) |
| Enable | Disable \| Upgrade \| Unload |
| Disable | Enable \| Unload \| Upgrade |
| Unload | Remove \| Register (re-init) |

---

## Rules

1. Enable never skips Health Check in production.  
2. Upgrade must not rewrite ADOS Core.  
3. Disable is preferred over Remove for incident response.  
4. AI Plugins: Disable emits agent stop signals via Runtime.

---

## Related

[[PLUGIN_MANAGER implied via SDK_OVERVIEW]] · [[PERMISSION_MODEL]] · [[HOOK_SYSTEM]] · [[../runtime/AGENT_RUNTIME|AGENT_RUNTIME]]

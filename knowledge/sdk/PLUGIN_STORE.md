---
title: ADOS Plugin Store
aliases:
  - Plugin Store
  - Enterprise Marketplace
tags:
  - sdk
  - marketplace
  - plugins
status: foundation
---

# ADOS Plugin Store (Enterprise Marketplace)

## Purpose

Describe the **Enterprise Marketplace**—how plugins are discovered, verified, signed, reviewed, checked for compatibility, and updated—so extension remains trustworthy without Core changes.

SDK: [[SDK_OVERVIEW]] · Lifecycle: [[PLUGIN_LIFECYCLE]] · Manifest: [[PLUGIN_MANIFEST]]

---

## Capabilities

### Plugin Discovery

- Catalog by type, capability, author, edition.  
- Search aligned with Knowledge Index tags where published.  
- Internal private store + partner public store tiers.

### Plugin Verification

- Manifest schema validation.  
- Dependency and Compatibility resolution.  
- Malware/policy scan; permission reasonableness review.  
- Provider Plugins checked against UPP interface rules (no domain logic).

### Digital Signatures

- Artifacts signed by publisher; Store countersigns for “verified” badge.  
- Enterprise editions require valid signature chain to Install/Enable.  
- Signature break → block Upgrade/Enable; alert Owner.

### Reviews

- Operator/Security/Architect reviews for sensitive types (Security, Secret Access, Business).  
- Customer ratings optional; do not replace verification.  
- Review outcomes stored in Decision/Knowledge memory when material.

### Compatibility

- Matrix: SDK version, OS, Runtime, edition.  
- Incompatible plugins hidden or marked non-installable.  
- Aligns with Manifest Compatibility field.

### Automatic Updates

- Opt-in channels: security patches vs minor vs major.  
- Auto-Update runs Upgrade lifecycle with Health Check; rollback on failure.  
- Major/breaking never silent in production without Admin policy.

---

## Trust tiers

| Tier | Meaning |
|------|---------|
| **Unsigned local** | Dev only; blocked in hardened enterprise |
| **Signed publisher** | Identity known |
| **Store verified** | Scanned + countersigned |
| **Enterprise approved** | Tenant Admin/Security grant template pre-approved |

---

## Store ↔ Runtime/OS

```text
Discover → Verify/Sign → Install → Register → …
Plugin Manager enforces Store policy at Enable
```

Marketplace metadata may appear as Knowledge Graph nodes (Plugin, Author, Review).

---

## Rules

1. Store cannot modify ADOS Core—only distribute plugins.  
2. Automatic Updates never apply unsigned builds.  
3. Permission escalation in an Upgrade requires re-grant.  
4. Yanked plugins: Disable push + advisory to tenants.

---

## Related

[[PLUGIN_SYSTEM]] · [[PERMISSION_MODEL]] · [[../memory/KNOWLEDGE_INDEX|KNOWLEDGE_INDEX]] · [[../providers/SUPPORTED_PROVIDERS|SUPPORTED_PROVIDERS]]

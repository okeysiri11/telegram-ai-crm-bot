---
title: ADOS Agent Registry
aliases:
  - Agent Registry
  - Factory Registry
tags:
  - agent-factory
  - registry
  - governance
status: foundation
---

# ADOS Agent Registry

## Purpose

The **Agent Registry** is the central inventory of all ADOS agents governed by the Factory.

If an agent is not in the registry, it is **not an official ADOS agent**—regardless of prompts that exist elsewhere.

Factory: [[AGENT_FACTORY]] · Lifecycle: [[AGENT_LIFECYCLE]] · Types: [[AGENT_TYPES]]

---

## Registry record schema

Every row / entry contains:

| Field | Description | Required |
|-------|-------------|----------|
| **Agent ID** | Stable unique id (`agt_<slug>`) | Yes |
| **Name** | Official display name | Yes |
| **Role** | Primary role title | Yes |
| **Owner** | Accountable human or role | Yes |
| **Version** | SemVer string | Yes |
| **Status** | Lifecycle stage | Yes |
| **Dependencies** | Other agents, modules, providers | Yes (may be `none`) |
| **Capabilities** | Verbs the agent may perform | Yes |
| **Permissions** | Access scopes (least privilege) | Yes |
| **Review Status** | Not started / In review / Approved / Blocked / Changes requested | Yes |

### Recommended extended fields

| Field | Description |
|-------|-------------|
| Type | Category from [[AGENT_TYPES]] |
| Spec path | Path to knowledge spec page |
| Contract version | Linked [[../agents/AGENT_CONTRACT|AGENT_CONTRACT]] revision |
| KPIs | Pointers to KPI definitions |
| Created / Updated | Timestamps |
| Successor ID | For Deprecated agents |

---

## Status values

Must match [[AGENT_LIFECYCLE]]:

`Draft` · `Training` · `Testing` · `Review` · `Approved` · `Production` · `Deprecated` · `Archived`

---

## Review Status values

| Value | Meaning |
|-------|---------|
| Not started | No formal review yet |
| In review | Chain in progress |
| Changes requested | Returned to author |
| Blocked | Security/architecture block |
| Approved | Gate passed for current version |

Review Status is **orthogonal** to lifecycle Status (e.g. Testing + In review).

---

## Uniqueness rules

Before insert:

1. Search by Name and Mission overlap.  
2. Search Capabilities for colliding ownership.  
3. If overlap exists → extend existing agent or split via Architect decision—**do not duplicate**.  

Enforced by [[FACTORY_RULES]].

---

## Example registry table (illustrative)

| Agent ID | Name | Role | Owner | Version | Status | Dependencies | Capabilities | Permissions | Review Status |
|----------|------|------|-------|---------|--------|--------------|--------------|-------------|---------------|
| `agt_enterprise_architect` | Enterprise Architect | Enterprise Architect | Orchestrator | 1.0.0 | Production | Core architecture docs | decide, review | read:architecture; escalate | Approved |
| `agt_example_draft` | Example Draft Agent | Domain Specialist | Knowledge Engineer | 0.1.0 | Draft | none | draft_spec | read:knowledge | Not started |

> Engineering Organization role specs under `knowledge/agents/roles/` should be mirrored into the registry when activated as runtime agents.

---

## Registry operations

| Operation | Who | Notes |
|-----------|-----|-------|
| Create row | Knowledge Engineer / author | Status=Draft |
| Update version | Owner | May require re-review |
| Advance status | Orchestrator (per lifecycle) | Evidence required |
| Deprecate | Orchestrator + owner | Successor recommended |
| Archive | Knowledge Engineer | After dependents cleared |

---

## Logical storage

This document defines the **schema and governance**.  
Physical storage may be a markdown table, YAML catalog, or future platform registry module—without changing this contract.

Canonical documentation home: `knowledge/agent_factory/AGENT_REGISTRY.md` (this file) plus per-agent specs.

---

## Related

[[AGENT_GENERATION_GUIDE]] · [[AGENT_TEMPLATE]] · [[FACTORY_RULES]] · [[../agents/ENGINEERING_ORGANIZATION|ENGINEERING_ORGANIZATION]]

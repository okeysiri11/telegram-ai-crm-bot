---
title: Documentation Standards
aliases:
  - Documentation Standards
tags:
  - standards
  - knowledge-1.1
generated: 2026-07-22
sprint: Knowledge 1.1
---

# Documentation Standards

## Overview
Every knowledge Markdown page in this vault follows a mandatory section contract for Obsidian living documentation.

## Architecture
Pages are notes with YAML frontmatter (`title`, `aliases`, `tags`) plus wiki links for graph connectivity.

## Components
Required sections (in order):
1. Overview
2. Architecture
3. Components
4. Relationships
5. Responsibilities
6. Interfaces
7. REST APIs
8. Events
9. Future roadmap
10. References
11. Related pages

## Relationships
Enforced by authors and the Knowledge generator templates — [[automation/DOCUMENTATION_AUTOMATION]].

## Responsibilities
Authors must keep sections present even if content is `N/A`, and must use `[[Wiki Links]]` for backlinks.

## Interfaces
Obsidian properties + Markdown headings.

## REST APIs
Document real prefixes when applicable; otherwise state N/A.

## Events
Document domain events or `N/A`.

## Future roadmap
Lint script for missing sections in Knowledge 1.2.

## References
[[INDEX]] · [[README]]

## Related pages
[[DASHBOARD]] · [[templates/Documentation Page]]

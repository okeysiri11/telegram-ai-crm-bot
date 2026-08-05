---
title: ADOS Runtime Server Implementation 1.5
aliases:
  - Runtime Server Implementation
tags:
  - ados-os
  - runtime
  - http
status: active
---

# ADOS Runtime Server (Sprint OS 1.5)

## Location

`src/kernel/runtime/` — production TypeScript (`@ados/kernel` **1.4.0**, platform banner **1.1.0**).

Docs in package:

- `src/kernel/docs/RUNTIME_SERVER.md`
- `src/kernel/docs/SERVER_ARCHITECTURE.md`
- `src/kernel/docs/BOOT_SEQUENCE.md`

## Boot from repository root

```bash
npm install
npm run build
npm run ados
```

Then:

```bash
curl http://localhost:3000/health
curl http://localhost:3000/status
```

## Architecture

```text
Kernel → Event Bus → Service Mesh → Workflow Engine → Runtime Server
```

No business-module imports.

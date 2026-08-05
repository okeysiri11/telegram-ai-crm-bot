# Interaction Runtime API

**Prefix:** `/api/enterprise-interaction/v1`  
**Sprint:** 29.6

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health |
| GET | `/inventory` | Catalog |
| GET | `/sessions` | Interaction sessions |
| GET | `/selection` | Selection state |
| GET | `/search?q=` | Global search |
| GET | `/navigation` | Navigation history |
| GET | `/actions` | Context actions |
| GET | `/history` | Interaction history |

## Client

```ts
import { interactionRuntime } from "@/runtime/interactionRuntime";

interactionRuntime.startup();
interactionRuntime.select("building", "hub");
interactionRuntime.execute("create_meeting");
interactionRuntime.search("Demo");
interactionRuntime.open("company", "biz_demo_corp");
```

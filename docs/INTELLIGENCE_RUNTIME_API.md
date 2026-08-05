# Intelligence Runtime API

**Prefix:** `/api/enterprise-intelligence/v1`  
**Sprint:** 29.7  
**Policy:** advisory only

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health + advisory flags |
| GET | `/inventory` | Catalog + policy |
| GET | `/insights` | Insights |
| GET | `/recommendations` | Recommendations (approval required) |
| GET | `/trends` | Trends |
| GET | `/risks` | Risks |
| GET | `/analytics` | Aggregated analytics snapshot |

## Client

```ts
import { intelligenceRuntime } from "@/runtime/intelligenceRuntime";

intelligenceRuntime.startup();
const cycle = intelligenceRuntime.analyze({ force: true });
// Never auto-runs:
intelligenceRuntime.executeRecommendation(id); // always forbidden
// Act via Interaction Runtime / Workflow with explicit approval instead.
```

# Creative Prompt Library

**Sprint:** 27.9 · **MVP deepen:** 32.0 · UI: Production Center → Prompts  
**Distinct from:** AI Builder Studio agent `PROMPT_LIBRARY`

## Features

- Categories · folders via `promptCollections`  
- Versioning + history (`bumpPromptVersion`)  
- Favorites · Search · Tags  
- Variables (`{{product}}`, brand-injected `{{tone}}`, `{{colors}}`, …)  
- Reuse via pipeline attach · Brand / company prompts  

## Data

Stored in `useProductionStore.prompts` (session key `ews_ai_production_v1`).

## Sprint 32.0

Brand Kit variables merge into `generateInStudio`. Generation records store resolved prompt + provider cost meter.

## Future

Semantic search via `platform_memory` · shared corporate vault · provider-side eval harness.

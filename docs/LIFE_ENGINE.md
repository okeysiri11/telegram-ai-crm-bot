# Enterprise Life Engine

**Sprint:** 29.2  
**Package:** `src/web/src/runtime/lifeEngine/`  
**API:** `/api/enterprise-life/v1`  
**Version:** `29.2`

## Role

Connects Digital Citizens · Business Network · City · AI · Automation · Workflows into one **living** runtime. Events come from real platform activity — not scripted City animations.

## Architecture

```
Citizen / EBN / Workflow / Automation
              │
              ▼
        Life Engine
  Events · Timeline · Occupancy
  Movement · Meetings · Projects
              │
   EventBus life_engine_update + city_update
              │
        Enterprise City Runtime API
```

## City Runtime API

`lifeEngine.cityRuntime()` returns:

- Current citizens + life presence  
- Building occupancy  
- Meetings · vehicles · activities  
- AI · projects · movements  

## Related

- [`LIFE_ENGINE_API.md`](./LIFE_ENGINE_API.md)
- [`SPRINT_29_2_RESULT.md`](./SPRINT_29_2_RESULT.md)
- [`DIGITAL_CITIZEN.md`](./DIGITAL_CITIZEN.md)
- [`BUSINESS_NETWORK.md`](./BUSINESS_NETWORK.md)

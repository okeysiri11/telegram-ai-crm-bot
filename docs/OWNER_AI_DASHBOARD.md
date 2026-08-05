# Owner AI Dashboard

**Sprint:** 30.5  
**Component:** `OwnerAiDashboard.tsx`  
**Mounted on:** `/owner` · `/ai-agents` (Owner Mode)

## God Mode capabilities

- See every running AI task  
- Force stop  
- Restart  
- Assign priority  
- Monitor resource usage (CPU/GPU projection)  
- View execution logs  

Gated by role switcher `isOwnerView()` / elevated roles. Does not bypass API auth — navigation/ops visibility for Beta.

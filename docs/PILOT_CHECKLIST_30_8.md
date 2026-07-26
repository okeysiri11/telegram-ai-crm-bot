# Beauty Pilot Checklist — Sprint 30.8

## Pre-flight

- [ ] Backend serving Hub Beauty routes (BOS/BWS/BCJ)  
- [ ] Platform Builder Concierge + Mission Control healthy  
- [ ] Observability (`enterprise-obs`) reachable  
- [ ] Comms Center writable  
- [ ] Web `VITE_API_PROXY` points at API host  
- [ ] Staff can login via `/login` (ISAM; JWT optional)

## Workflow validation

- [ ] Open `/workspace/beauty`  
- [ ] Execute Beauty workflow end-to-end  
- [ ] All steps show **ok**  
- [ ] Appointment / booking id present in log  
- [ ] Mission Control probe succeeds  
- [ ] OBS audit + metric recorded  
- [ ] Pilot Dashboard shows updated workflow metrics  

## Platform reuse audit

- [ ] Auth is shared (no Beauty login stack)  
- [ ] Concierge sessions use PB prefix  
- [ ] Notifications use enterprise-comms  
- [ ] Automotive `/workspace/auto` still works unchanged  

## Sign-off

- [ ] Internal Beauty pilot approved for continuous use alongside Automotive  

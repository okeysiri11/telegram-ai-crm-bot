# Owner City Mode (God Mode)

**Sprint:** 30.4  
**Gate:** Role switcher `isOwnerView()` (role `owner`)

## Capabilities

When Owner Mode is active on `/enterprise-city`:

1. **Open every district** — full district chip row in Owner panel  
2. **Jump to any building** — building short-name chips (select + camera)  
3. **Platform health** — glance OK / attention / critical / AI counts  
4. **Active users** — sum of `buildingOps(...).activeUsers` across catalog  
5. **Runtime status** — `runtimeEngine.getSnapshot()` summary + compact runtime monitor  

## UX

Panel title: **Owner Mode · God Mode**. Non-owners do not see the panel; standard City chrome remains available.

## Security note

This is a **navigation / visibility** God Mode for platform owners in Beta — not a bypass of API authorization. Module routes still use existing guards.

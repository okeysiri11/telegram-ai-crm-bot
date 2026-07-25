# Platform Control Center

Sprint **28.7** / Platform Builder **v1.6.0** / Control Center **1.0**

Enterprise Platform Control Center powered by God Mode expansion.

## Module

Platform Builder → God Mode → Platform Control Center

API prefix: `/api/platform-builder/v1/god-mode/control/`

## Enterprise design

Dark Mode · Responsive · Animations · Universal Builder Framework step studio.

## Capabilities

| Surface | Purpose |
| --- | --- |
| Overview | Counts for Organizations, Users, AI, Concierges, Verticals, Departments, Modules, Knowledge, Workflows, Marketplace, Registries, Visual Layer |
| Global Search | AI · Organizations · Documents · Knowledge · Registry · Users · Dashboards · Workflows · Marketplace |
| Object Inspector | Internal ID · Visual ID · Type · Owner · Dependencies · Relationships · Lifecycle · Status · History |
| Live Editor | Properties · Permissions · Knowledge · Relationships · Dependencies · Metadata |
| Global Registry | Browse · Search · Filter · Repair · Rebuild · Synchronize |
| System Health | Services · Modules · Performance · Registry Status · Synchronization · AI Status · Memory Usage |
| Diagnostics | Broken Links · Missing Dependencies · Registry Problems · Invalid References · Configuration Issues + repair recommendations |
| Architecture Explorer | Module · AI · Knowledge · Workflow · Registry · Future Visual Layer graphs |
| Audit Center | Who · What · When · Rollback · Version History |
| Explain Mode | Reason · Expected Benefit · Business Impact · Alternatives · Estimated Effect |
| Create | Register Diagnostics, Audit, Architecture snapshot, Health Center |

## Layout

- Backend: `applications/platform_builder/control_center/`
- Frontend: `src/web/platform-builder/god-mode/ControlCenterStudio.tsx`
- Knowledge: `knowledge/platform_builder/control_center/`
- Docs: [GOD_MODE.md](./GOD_MODE.md)
- Tests: `tests/test_platform_control_28_7.py`

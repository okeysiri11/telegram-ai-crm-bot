# Module Registry (Enterprise Shell)

**Sprint:** 28.5  
**API:** `shellModuleRegistry` in `src/web/src/shell/enterprise/shellModuleRegistry.ts`  
**Version:** `SHELL_MODULE_REGISTRY_VERSION = "28.5"`

## Purpose

Dynamic shell-facing module registry that **projects** `ENTERPRISE_MODULES` (module catalog) plus Desktop, and accepts **dynamic** registrations for future modules. It does not replace the workspace `moduleRegistry` or the catalog — it bridges them into shell nav and search.

## Built-in modules

Dashboard · Desktop · Enterprise City · CRM · ERP · Projects · AI Studio · Production Center · AI Agents · Knowledge · Documents · Marketplace · Automation · Analytics · Integrations · Security · Settings

## API

```ts
shellModuleRegistry.list()
shellModuleRegistry.get(id)
shellModuleRegistry.byCategory(category)
shellModuleRegistry.toNavItems()
shellModuleRegistry.searchDocs()
shellModuleRegistry.register(module)   // source → "dynamic"
shellModuleRegistry.unregister(id)
shellModuleRegistry.subscribe(listener)
```

## Categories

`core` · `business` · `ai` · `ops` · `platform` · `system`

## Registration pattern

```ts
shellModuleRegistry.register({
  id: "my_module",
  label: "My Module",
  route: "/my-module",
  icon: "dashboard",
  category: "ops",
  keywords: ["my", "module"],
  source: "dynamic",
});
// Call refreshShellSearch() so Command Palette / Search Workspace pick it up.
```

Unload dynamic modules via `enterpriseShellRuntime.unloadModule(id)` (catalog modules stay registered).

## Search

`refreshShellSearch()` upserts:

- All shell modules  
- Production projects / prompts / generations (when store available)  
- Settings runtime doc  

Quick actions are registered separately via `registerQuickActionsInSearch()`.

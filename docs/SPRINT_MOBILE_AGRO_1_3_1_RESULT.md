# Sprint MOBILE AGRO 1.3.1 — «Открыть панель» opens the ops panel

## Root cause

«Открыть панель» was a **route**, not a panel.

Click path before this fix:

`button` → `onClick={() => navigate(href)}` → `operationalPanelPath(agro)` = `/workspace/agro`

That is the same destination as «Открыть рабочее пространство». The operational menu (19 Agro cabinet items) never opened. The previous “Dead buttons: 0” report was invalid for real-phone acceptance.

Not disabled. Not pointer-events. Not z-index. Wrong action.

## Fix

- «Открыть рабочее пространство» → `/workspace/agro` (enter the workspace)
- «Открыть панель» → `setDrawerOpen(true)` (existing operational drawer, source `AGRO_OPS_NAV`)

Same nav as desktop Agro cabinet. No second duplicated Agro list.

## Also in 1.3.1

- Selected Agro persists (`verticalWorkspaceStore`); home CTAs use that id
- Home workspace path stays `/workspace/agro`, not `/vertical/agro`
- Deep links `/workspace/agro?view=accounting` and `?view=counterparties` stay on the public SPA
- Android back still closes the open panel first
- Desktop Agro landing (≥768px) unchanged

## Public HTTPS (current)

https://february-taylor-environmental-positioning.trycloudflare.com

Verified 200: `/dashboard`, `/workspace/agro`, `?view=accounting`, `?view=counterparties`. Live `MobileHome` handler over that URL is `setDrawerOpen(true)`.

TEMPORARY tunnel: laptop must stay on.

MOBILE AGRO 1.4 was not started.

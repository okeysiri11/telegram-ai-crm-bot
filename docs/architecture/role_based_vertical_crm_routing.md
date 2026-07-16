# Role-Based Vertical CRM Routing — architecture foundation

## Canonical roles

| Role | User (example) | Scope |
|------|----------------|-------|
| `SUPER_ADMIN` | Ton (`OWNER_ID`) | All verticals, admin panel, reassign leads |
| `AUTO_MANAGER` | Борода (`DEFAULT_AUTO_MANAGER_ID`) | `vertical=auto` leads |
| `AGRO_MANAGER` | Christopher (`DEFAULT_AGRO_MANAGER_ID`) | `vertical=agro` leads |
| `CLIENT` | Luc (entry-link clients) | Client menu of entry vertical only |

Defined in `services/system_roles.py`.

## Verticals

`auto` · `agro` · `realty` · `logistics`

## Routing

```
lead.vertical == "auto"  → AUTO_MANAGER subscription (Борода)
lead.vertical == "agro"  → AGRO_MANAGER subscription (Christopher)
```

Resolution order (`VerticalRoutingEngineV1`):

1. Active row in `manager_vertical_subscriptions_v1` (primary first)
2. Config fallback: `DEFAULT_AUTO_MANAGER_ID` / `DEFAULT_AGRO_MANAGER_ID`

## Manager subscriptions

Table `manager_vertical_subscriptions_v1` + denormalized `users.verticals` JSONB.

Future: one manager can subscribe to multiple verticals.

## SUPER_ADMIN menu

`keyboards.super_admin_menu()` — no client scenarios.

## Safe rollout

1. Apply migration `f9w345678901`
2. Set `DEFAULT_AGRO_MANAGER_ID` in `.env`
3. Restart bot — startup seeds roles/subscriptions
4. AUTO client flows unchanged; assignment still reaches Борода via `vertical=auto`
5. Gradually map CRM statuses to `ManagerLeadStatus` (NEW/TAKEN/…)
6. Wire SUPER_ADMIN filter screens (all leads / by vertical / reassign)

## Conflicts with existing architecture

- Multiple role systems: permission_engine + RBAC v2 + legacy SQLite
- `LeadEngineStatus` ≠ `ManagerLeadStatus` (mapped later)
- `OWNER` still seeded for SUPER_ADMIN for legacy gates
- Dealer manager remains parallel (`DEFAULT_DEALER_MANAGER_ID`)

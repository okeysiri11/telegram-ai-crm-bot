# First User Experience — Sprint 32.3.1

## Flow

`/login` → (if incomplete) `/onboarding/first-entry` → `/dashboard`

1. Welcome  
2. Role selection (extensible catalog)  
3. Workspace creation (Tenancy + EWS)  
4. Workspace ready  
5. AI Team choice → existing AI Team Center  
6. AI Concierge profile → existing Concierge Builder  
7. Open Dashboard  

## Reuse

- Workspace Engine: tenancy `/workspaces`, EWS bootstrap, `workspaceStore`  
- AI Team: `/platform-builder/ai-team`  
- Concierge: catalog + `/platform-builder/concierge`  
- Dashboard: existing `/dashboard`  
- ProgressIndicator, EDS Button/Card/Input/Select  

## Extension

`firstEntryRoleCatalog.register({...})` adds roles without architecture changes.

Settings → Personalization scaffold for themes/widgets/AI preferences in later sprints.

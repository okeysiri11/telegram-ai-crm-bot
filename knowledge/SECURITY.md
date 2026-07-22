# Security


---
[[INDEX]] · [[PLATFORM_CORE]] · [[ARCHITECTURE]] · [[API_REFERENCE]]


## Overview
Platform security layer **1.0** (Sprint **5.1**) covers authentication/authorization integration, hardened admin surfaces, and certification security controls. Application middlewares optionally authenticate via platform bridges.

## Architecture
- Core: `platform_security`, identity hooks, management authorization
- Apps: API middleware + bridge `authenticate_request` patterns
- Ecosystem: governance, compliance, audit (Sprint 7.6)
- Certification artifacts: `docs/SECURITY.md`, `docs/CERTIFICATION_SECURITY.md`

## Components
- Security layer / auth principals
- Permission models (platform + ecosystem + app roles)
- Audit and compliance (Ecosystem governance)
- Plugin trust boundaries ([[PLUGIN_SDK]])

## Relationships
- Cross-cuts [[PLATFORM_CORE]], Ecosystem, and all apps
- Deployment hardening in [[DEPLOYMENT]]
- Roles docs also in repository `docs/ROLES_AND_PERMISSIONS.md`

## APIs
Auth token issuance on legacy `/api/auth/token`; app routes may require `Authorization` headers. Management routes enforce elevated auth.

## Future roadmap
Unified OIDC/SSO across Ecosystem tenants and partner APIs ([[ROADMAP]]).

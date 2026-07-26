# Pilot Checklist — Sprint 30.4

## Platform-level gate (required before any pilot)

- [x] Shared application shell operational  
- [x] Permission-aware navigation  
- [x] Module loader for seven ecosystems  
- [x] Mission Control reachable from shell / portals  
- [x] Session → API header bridge (`apiFetch`)  
- [x] Telemetry to Enterprise Observability  
- [x] Error boundary reports errors  
- [x] Loading screen on boot  
- [ ] Staging deploy per Deploy Topology  
- [ ] Real ISAM/EIC JWT validation (demo tokens OK for controlled internal pilot only)

## Per-ecosystem readiness

| Ecosystem | Readiness | Missing | Critical blockers | Recommended pilot scope | Expected feedback | Success metrics |
|-----------|-----------|---------|-------------------|-------------------------|-------------------|-----------------|
| **Automotive** | Shell + APIs exist | Live customer/dealer data views | Identity JWT + OpenAPI freeze | 1 dealer + 5 customers: browse inventory / lead capture | UX friction, missing fields | Task completion ≥70%; error rate &lt;5% |
| **Beauty** | Shell + libraries | Product facade UI | Booking workflow not bound | Staff roster view only | Which BOS screens matter | Time-to-first-action &lt;2m |
| **Cafe** | Shell / catalog | Product application | No cafe domain app yet | Menu + order **read-only** mock via shell feedback | Must-have POS vs CRM | Prioritize P0 cafe stories |
| **Agriculture** | Shell + agro APIs | Operator workflows in web | Trade/port depth | Grain lot list for one tenant | Field vs office needs | API errors &lt;2% on list |
| **Drone** | Shell / catalog | Domain workflows | No drone ops UI | Fleet status placeholder feedback | Mission planning vs maintenance | Rank top 3 workflows |
| **Legal** | Shell + legal-enterprise | Matter UI binding | Document pipeline depth | Matter list for one firm | Privilege / audit concerns | Audit log coverage 100% of opens |
| **Crypto (Bidex)** | Shell + crypto-enterprise | Trading UI binding | Compliance / KYC gates | Read-only portfolio summary | Trust / latency | p95 API &lt;800ms |

## Controlled pilot rules

1. One ecosystem per pilot wave  
2. Telemetry enabled  
3. Demo tenants only until JWT validation is live  
4. No architecture forks during pilot feedback  

## Sign-off

| Role | Sign-off |
|------|----------|
| Platform owner | Shell + telemetry OK |
| Ecosystem owner | Pilot scope accepted |
| Security | Demo-token risk accepted for internal pilot |

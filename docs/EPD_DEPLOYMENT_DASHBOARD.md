# EPD — Deployment Gate, Dashboard & Reports

**Sprint:** 25.6

## Deployment validator (pre-release)

Migrations · Backups · Version compatibility · Tests · Security · Performance · Fault tolerance  
Integrates EMR / ESV / ETI / EPL / ECE — does not duplicate their logic.

## Dashboard

System Health · Active Services · Infrastructure · Monitoring · Alerts · Logs · Metrics · Deployments · Capacity · Availability

## Reports

Production · Health · Monitoring · Capacity · Availability · Deployment

## Gate rule

`release_blocked=true` when health fails, critical alerts fire, or deployment checks fail → Production not allowed.

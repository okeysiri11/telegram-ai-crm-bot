# Upgrade Guide

## From 4.2.0-enterprise → 4.2.0-enterprise

1. Pull Sprint 13.9 certification package
2. No data migration required for in-memory sprint stores
3. Re-run regression suite (`tests/test_*13_*.py`)
4. Confirm readiness flags on `/api/enterprise-certification/v1/health`

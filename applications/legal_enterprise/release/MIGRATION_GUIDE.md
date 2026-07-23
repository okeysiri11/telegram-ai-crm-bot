# Migration Guide

## From 4.9.7-enterprise → 5.0.0-enterprise

1. Deploy Sprint 17.8 certification package (additive; no prior Legal module changes).
2. Update clients to accept `application_version: 5.0.0-enterprise`.
3. Point monitoring at `/api/legal-enterprise-certification/v1/health`.
4. Run certification bootstrap and archive the scorecard.
5. No data migration required for in-memory EntityStore buckets; persistent deployments should snapshot before cutover.

## Compatibility

All prior Legal API prefixes remain available and unchanged in path shape.

# Migration Guide

## From 5.1.7-enterprise → 5.2.0-enterprise

1. Deploy Sprint 18.8 certification package (additive; no prior Finance module source changes required beyond shared wiring).
2. Update consumers expecting `application_version` to `5.2.0-enterprise`.
3. Foundation string becomes `Enterprise Platform v5.1.7-enterprise`.
4. Enable certification API `/api/finance-enterprise-certification/v1`.
5. Run certification bootstrap and confirm Production Ready.

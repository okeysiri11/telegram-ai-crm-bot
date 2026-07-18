# Dependency Certification

> Generated: 2026-07-18 13:53:32 UTC

## Verdict: **FAIL**

## Graph Metrics

| Metric | Value |
|--------|------:|
| Modules | 802 |
| Edges | 2621 |
| All cycles | 84 |
| Strict governance cycles | 0 |

## Cycle Categories

- **config_legacy**: 18
- **legacy_pg_engines**: 44
- **orm_models**: 9
- **other**: 6
- **platform_core**: 7

## Governed-Layer Cycles

- cycle: platform_legacy.feature_flags -> platform_configuration.configuration_center -> platform_legacy.feature_flags
- cycle: services.role_service -> platform_identity.role_service -> platform_legacy -> platform_legacy.migration_report -> platform_legacy.registry -> platform_legacy.adapter -> services.pg_manager_delivery_engine -> services.pg_entry_point_engine
- cycle: database.models.users -> database.models.user_role -> database.models.users
- cycle: database.models.user_role -> database.models.role -> database.models.user_role
- cycle: database.models.permissions -> database.models.roles -> database.models.permissions
- cycle: database -> services.role_service -> platform_identity.role_service -> platform_legacy -> platform_legacy.migration_report -> platform_legacy.registry -> platform_legacy.adapter -> services.pg_manager_delivery_engine
- cycle: database -> services.role_service -> platform_identity.role_service -> platform_legacy -> platform_legacy.migration_report -> platform_legacy.registry -> platform_legacy.adapter -> services.pg_manager_delivery_engine
- cycle: database -> services.role_service -> platform_identity.role_service -> platform_legacy -> platform_legacy.migration_report -> platform_legacy.registry -> platform_legacy.adapter -> services.pg_manager_delivery_engine
- cycle: database -> services.role_service -> platform_identity.role_service -> platform_legacy -> platform_legacy.migration_report -> platform_legacy.registry -> platform_legacy.adapter -> services.pg_manager_delivery_engine
- cycle: platform_legacy -> platform_legacy.migration_report -> platform_legacy.registry -> platform_legacy.adapter -> services.pg_manager_delivery_engine -> services.pg_auto_client_request_engine -> services.pg_client_request_crm_engine -> services
- cycle: database -> services.role_service -> platform_identity.role_service -> platform_legacy -> platform_legacy.migration_report -> platform_legacy.registry -> platform_legacy.adapter -> services.pg_manager_delivery_engine
- cycle: database -> services.role_service -> platform_identity.role_service -> platform_legacy -> platform_legacy.migration_report -> platform_legacy.registry -> platform_legacy.adapter -> services.pg_manager_delivery_engine
- cycle: database -> services.role_service -> platform_identity.role_service -> platform_legacy -> platform_legacy.migration_report -> platform_legacy.registry -> platform_legacy.adapter -> services.pg_manager_delivery_engine
- cycle: database -> services.role_service -> platform_identity.role_service -> platform_legacy -> platform_legacy.migration_report -> platform_legacy.registry -> platform_legacy.adapter -> services.pg_manager_delivery_engine
- cycle: database -> services.role_service -> platform_identity.role_service -> platform_legacy -> platform_legacy.migration_report -> platform_legacy.registry -> platform_legacy.adapter -> services.pg_manager_delivery_engine

## Deferred Legacy Cycles (Sprint 2)

Legacy `services/pg_*` engine cycles (~45) are isolated compatibility code.
Breaking these without behavior change requires adapter extraction in Sprint 2.
Config ↔ legacy cycles (~21) require feature-flag decoupling.


# Builder SDK

Sprint **28.5** / Platform Builder **v1.4.0**

Internal Builder SDK foundation on top of the Universal Builder Framework.

## Status

Architecture + callable Framework APIs. Packaged SDK distribution arrives later.

## Planned / available APIs

- `define_builder(schema)`
- `register_steps(builder_id, steps)`
- `attach_validation(builder_id, rules)`
- `attach_components(builder_id, components)`
- `save_template(builder_id, config)`
- `clone_builder(builder_id)`
- `run_lifecycle(session_id / builder_type)`

## HTTP

- `GET /api/platform-builder/v1/ubf/sdk`
- `POST /api/platform-builder/v1/ubf/sdk/define`

## Goal

Allow future Builders to be created with minimal development effort using one shared lifecycle, validation, preview, registry, and template pipeline.

## Layout

- Backend: `applications/platform_builder/framework/sdk.py`
- Knowledge: `knowledge/platform_builder/sdk/`
- Tests: `tests/test_builder_sdk_28_5.py`

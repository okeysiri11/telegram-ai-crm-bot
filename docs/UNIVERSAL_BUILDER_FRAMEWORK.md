# Universal Builder Framework

Sprint **28.5** / Platform Builder **v1.4.0**

One common architecture for every Builder in the platform.

## Module

Platform Builder → Universal Builder Framework (`/platform-builder/framework`)

API: `/api/platform-builder/v1/ubf/*`

## Lifecycle

Initialize → Configure → Validate → Preview → Summary → Create → Register → Finish

## UI components

Wizard · Cards · Forms · Progress Bar · Stepper · Preview Window · Summary Screen · Confirmation Screen · Live Validation · Animations

## Validation

Required Fields · Duplicate Detection · Registry Validation · Dependency Validation · Knowledge Validation · Relationship Validation · Live Error Detection · Suggestion Engine

## Live Preview Engine

Instant Preview · Live Update · Realtime Validation · Visual Summary

## Builder Registry

Registers Builder Type, Version, Schema, Components, Templates, Validation Rules.

## Template Engine

Save as template · Clone · Duplicate configurations

## Extension System

Plugins · Custom Steps · Custom Validation · Custom Components · Future Marketplace Extensions

## Builder SDK

Foundation APIs for creating new Builders with minimal effort. See [BUILDER_SDK.md](./BUILDER_SDK.md).

## Target builders

AI · Concierge · Vertical · Workflow · CRM · ERP · Knowledge · Marketplace · Dashboard · Automation · Document · Department · User · Future

## Layout

- Backend: `applications/platform_builder/framework/`
- Frontend: `src/web/platform-builder/ubf/` + shared `framework/` components
- Knowledge: `knowledge/platform_builder/framework/`
- Tests: `tests/test_builder_framework_28_5.py`

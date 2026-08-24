# Sprint 50.3 — Crypto Operator Desk Completion (Plan)

## Goal

Finish operator desk depth: signal notifications, real calendar UI, complete paper-trading demo account, journal/traceability, cross-links, reliable localhost scripts. No real broker. No Telegram/email. No Sprint 50.4.

## Architecture

| Area | Approach |
|------|----------|
| Notifications | In-app store + browser Notification/Audio when permitted |
| Calendar | Client calendar UI aggregating macro/news/analysis/signals/paper + manual events API |
| Paper | Extend simulation engine: account ledger 100k USD, statuses DRAFT→CLOSED |
| Persistence | Extend `fx_mi_*` + in-memory fallback |
| Scripts | Harden run/stop with port reclaim + HTTP gates |

## Out of scope

Model training, real execution, Telegram/email delivery.

# Pilot Guide — Sprint 30.5

## Goal

Run the **first internal pilot** using the shared Web Core — not a production customer launch.

## Operator path

1. Login (demo owner account OK for internal pilot)
2. Open **Pilot** in top nav → `/pilot`
3. Confirm platform status, 7 ecosystems, OBS probes
4. Open **Mission Control** → verify live module panel
5. Open `/workspace/auto` (recommended first ecosystem)
6. Confirm telemetry events appear when OBS is mounted

## Success signals

| Signal | Where |
|--------|-------|
| Web Core ready | Pilot Dashboard |
| Ecosystems registered | Pilot + Mission Control live panel |
| Errors / warnings | Pilot Dashboard |
| API probes | Pilot refresh telemetry |
| Audit / page views | OBS `/logs` |

## Scope limits

- Demo tokens acceptable **only** for internal pilot
- No architecture changes during pilot feedback
- One ecosystem focus recommended (Automotive)

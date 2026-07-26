# Beauty Pilot Readiness — Sprint 30.8

## Missing features (non-blocking for internal pilot)

| ID | Item | Severity |
|----|------|----------|
| MF-30.8-1 | Rich salon calendar UI (drag/drop) beyond workflow probe | Low |
| MF-30.8-2 | Client self-service portal booking form (uses staff-run BCJ today) | Medium |
| MF-30.8-3 | Deep AMO campaign designer wired into Beauty page | Low |

## Critical issues

None blocking internal pilot if BOS/BWS/BCJ/OBS/Comms/PB health gates pass.

## UX improvements

| ID | Idea |
|----|------|
| UX-30.8-1 | Persist last client email for repeat pilot runs |
| UX-30.8-2 | Link appointment id from execution log to schedule view |
| UX-30.8-3 | Dual-pilot status strip on `/pilot` (auto vs beauty completion rates) |

## Production blockers (external pilot / multi-tenant)

| ID | Blocker |
|----|---------|
| PB-30.8-1 | External SMTP may be unset (Comms registration still proves the path) |
| PB-30.8-2 | Beauty portal auth parity with Automotive customer portal not required for staff pilot |
| PB-30.8-3 | Multi-salon tenant isolation hardening beyond Hub store |

## Verdict

**Ready for internal Beauty pilot** on the shared Enterprise Platform. Automotive remains the reference and is unchanged.

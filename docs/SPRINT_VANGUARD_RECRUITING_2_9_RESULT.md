# Sprint Vanguard Recruiting 2.9 — simplify lead → recruiter → candidate UX

**Date:** 2026-09-02  
**Status:** code complete; needs Render deploy of this commit

Phases 2.4–2.8 remain in place: HMAC ingest, persistence, owner→`ados` mapping, JWT, lead status, vacancy assign, convert idempotency, pipeline.

## ROOT_CAUSE_UX

The desk exposed every mutation as duplicated row buttons (`Назначить {name}`, qualify, convert) for several leads at once, plus a second convert control on the table. Operators had to know assignee slugs and `vacancy_id`. Converted was not visually terminal. Home showed task counts instead of the hiring sequence.

## What shipped

- One lead action panel: status, recruiter dropdown, vacancy dropdown, qualify, convert, note, reject.
- Recruiter list from real assignees + current session user (no fake directory).
- Convert still uses 2.8 `/convert` (idempotent). Converted leads show **Открыть кандидата**.
- Candidate panel: identity fields, pipeline stepper, **Открыть лид**.
- Home: new / qualified / candidates / interview / hired + linkable attention.
- Vanguard overview: four operational numbers + Открыть лиды / кандидатов / сайт.

## Architectural decisions

- No new CRM package. Dashboard gained additive `recruiters` / `attention_items` / card counts.
- Assign API now accepts empty assignee (Не назначен). Convert/HMAC/JWT unchanged.
- Email/phone still do not collapse independent leads.

## DB migrations

None.

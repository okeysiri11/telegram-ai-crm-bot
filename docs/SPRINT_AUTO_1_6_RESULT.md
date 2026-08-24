# Sprint AUTO 1.6 — result

## What shipped

Document OS on Auto: individual client fields, sale/registration packages, configurable checklist templates, DRAFT document generation, dossiers, validation, Telegram `/docs` + file upload on the existing bot, CSV register export, counters, analytics readiness, and status/deal-close warnings.

Primary surface:

- Backend mixin `services/auto_ops/documents.py` + catalog `services/auto_ops/documents_catalog.py`
- Additive `/api/auto-ops/v1/documents/*` (desk, packages, templates, generate, export, zip, dossiers, timeline, status, check)
- Frontend `src/web/workspace/auto/AutoDocumentsDesk.tsx`
- Existing Auto Telegram router (`/docs`, `F.document`, pending VIN)

## Architectural decisions

| Decision | Why | Rejected |
|---|---|---|
| Mixin on `AutoOpsService`, not a new `platform_*` | Extends existing Auto documents/files | Isolated document service |
| Keep 1.0 sidebar labels (Продажи, Платежи и расходы, CRM и задачи, Telegram, Отчёты) | 1.0 nav tests and compact menu | Replacing with «Сделки» / dropping Telegram |
| Packages live on vehicle profile + Документы, not new top-level items | Spec §48 | «Пакет продажи» / «Регистрация» in sidebar |
| Generation is placeholder DRAFT with disclaimer | Spec §21–23; no fake legal clauses | Invented Ukrainian statutory text |
| Signature status only, no e-sign provider | Spec §25 | Fake electronic signature |
| OCR optional filename VIN hint, confirm before canonical write | Spec §26–27 | Mandatory OCR / silent VIN relink |
| CSV export only | No XLSX library in Python requirements | Pretending XLSX works |
| ZIP dossier from org-scoped `files.py` paths | Local zipfile is safe | Fake download without files |
| Status/deal-close: warn + apply, privileged override audited | Spec §44–45; do not break 1.0–1.5 status updates | Hard-block transitions |

## Intentionally deferred / limitations

- No electronic signature provider.
- OCR is not a mandatory dependency; only regex VIN hints from filename/notes.
- XLSX export is not implemented.
- Generated files are UTF-8 `.txt` drafts, not Word/PDF legal forms.
- ZIP is available when files exist on the storage adapter; empty dossiers return an error rather than a fake archive.
- Company placeholders stay empty until admin fills Настройки → company profile. Nothing is hardcoded.

## Build / lint / tests

- Backend: **59 passed / 0 failed** (`test_auto_ops_1_0` … `1_6`; 1.6 adds 8 tests; 1.0–1.5 sprint sets accept `AUTO_1.6`).
- Frontend: **21 passed / 0 failed** (1.0×5 + 1.1×2 + 1.2×2 + 1.3×3 + 1.4×2 + 1.5×4 + 1.6×3).
- Frozen `/api/auto/v1` unchanged. Agro / Crypto / Beauty / Legal / Travel untouched.

## Follow-ups

AUTO 1.7 is out of scope for this sprint.

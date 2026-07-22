# Commercial release manager — notes/manifest certification helpers.

from __future__ import annotations

from pathlib import Path

from applications.auto_marketplace.config import DEFAULT_CONFIG


class CommercialReleaseManager:
    def notes_path(self) -> Path:
        return Path(__file__).resolve().parent / "RELEASE_NOTES.md"

    def certify(self) -> dict:
        notes = self.notes_path()
        text = notes.read_text(encoding="utf-8") if notes.exists() else ""
        return {
            "application_version": DEFAULT_CONFIG.application_version,
            "release_status": DEFAULT_CONFIG.release_status,
            "production_ready": DEFAULT_CONFIG.production_ready,
            "notes_present": "2.0.0" in text,
            "certified": DEFAULT_CONFIG.application_version == "2.0.0" and DEFAULT_CONFIG.production_ready,
        }

    def metrics(self) -> dict:
        return self.certify()


commercial_release_manager = CommercialReleaseManager()

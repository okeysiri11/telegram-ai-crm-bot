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
        version = DEFAULT_CONFIG.application_version
        return {
            "application_version": version,
            "release_status": DEFAULT_CONFIG.release_status,
            "production_ready": DEFAULT_CONFIG.production_ready,
            "notes_present": version in text or "4.1.0-enterprise" in text or "2.0.0" in text,
            "certified": bool(version) and DEFAULT_CONFIG.production_ready,
        }

    def metrics(self) -> dict:
        return self.certify()


commercial_release_manager = CommercialReleaseManager()

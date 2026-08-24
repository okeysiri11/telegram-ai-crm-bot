"""Lawyer file attachments — local blob store + Postgres metadata (Sprint 51.1 / 3.1)."""

from __future__ import annotations

import os
from pathlib import Path

ALLOWED_MIME = {
    "application/pdf": ".pdf",
    "application/msword": ".doc",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
    "image/jpeg": ".jpg",
    "image/jpg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}

ALLOWED_EXT = {".pdf", ".doc", ".docx", ".jpg", ".jpeg", ".png", ".webp"}


def storage_root() -> Path:
    raw = os.environ.get("LEGAL_OPS_FILES_DIR") or os.path.join(os.getcwd(), "data", "legal_ops_files")
    path = Path(raw)
    path.mkdir(parents=True, exist_ok=True)
    return path


def validate_upload(filename: str, mime_type: str | None) -> dict | None:
    ext = Path(filename or "").suffix.lower()
    if ext not in ALLOWED_EXT:
        return {
            "ok": False,
            "error": "validation",
            "message_ru": "Допустимы PDF, DOC, DOCX, JPG, JPEG, PNG, WebP",
        }
    if mime_type and mime_type.lower() not in ALLOWED_MIME and not mime_type.lower().startswith("image/"):
        if mime_type.lower() not in {
            "application/pdf",
            "application/msword",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        }:
            return {"ok": False, "error": "validation", "message_ru": "Неподдерживаемый тип файла"}
    return None


def write_bytes(organization_id: str, file_id: str, data: bytes) -> str:
    org_dir = storage_root() / organization_id
    org_dir.mkdir(parents=True, exist_ok=True)
    dest = org_dir / file_id
    dest.write_bytes(data)
    return str(dest)


def read_bytes(storage_path: str) -> bytes | None:
    p = Path(storage_path)
    if not p.is_file():
        return None
    return p.read_bytes()

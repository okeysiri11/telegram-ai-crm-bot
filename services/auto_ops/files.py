"""AUTO file attachments — local blob store + metadata (Legal/Agro pattern)."""

from __future__ import annotations

import os
from pathlib import Path

ALLOWED_EXT = {".pdf", ".doc", ".docx", ".xls", ".xlsx", ".jpg", ".jpeg", ".png", ".webp", ".txt"}
ALLOWED_MIME = {
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "image/jpeg",
    "image/jpg",
    "image/png",
    "image/webp",
    "text/plain",
}


def storage_root() -> Path:
    raw = os.environ.get("AUTO_OPS_FILES_DIR") or os.path.join(os.getcwd(), "data", "auto_ops_files")
    path = Path(raw)
    path.mkdir(parents=True, exist_ok=True)
    return path


def validate_upload(filename: str, mime_type: str | None) -> dict | None:
    ext = Path(filename or "").suffix.lower()
    if ext not in ALLOWED_EXT:
        return {
            "ok": False,
            "error": "validation",
            "message_ru": "Допустимы PDF, DOC, DOCX, XLS, XLSX, JPG, PNG, WebP, TXT",
        }
    if mime_type:
        mt = mime_type.lower()
        if mt not in ALLOWED_MIME and not mt.startswith("image/"):
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

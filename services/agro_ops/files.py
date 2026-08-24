"""AGRO file attachments — local blob store + registry metadata (AGRO 1.0).

Reuses the Legal Ops storage pattern (blob on disk, metadata in DB registry).
Files are NOT stored as base64 in the database.
"""

from __future__ import annotations

import os
from pathlib import Path

ALLOWED_EXT = {".pdf", ".doc", ".docx", ".xls", ".xlsx", ".csv", ".jpg", ".jpeg", ".png", ".heic", ".heif"}

ALLOWED_MIME_PREFIXES = ("image/",)
ALLOWED_MIME = {
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "text/csv",
    "application/csv",
}

DOCUMENT_TYPES = [
    ("contract", "Договор"),
    ("invoice", "Счёт"),
    ("specification", "Спецификация"),
    ("act", "Акт"),
    ("certificate", "Сертификат"),
    ("quality_certificate", "Сертификат качества"),
    ("phytosanitary", "Фитосанитарный документ"),
    ("cmr", "CMR"),
    ("ttn", "ТТН"),
    ("customs", "Таможенный документ"),
    ("tax", "Налоговый документ"),
    ("bank", "Банковский документ"),
    ("insurance", "Страховка"),
    ("photo", "Фото"),
    ("tech_passport", "Техпаспорт"),
    ("inspection", "Техосмотр"),
    ("permit", "Разрешение"),
    ("driver_license", "Водительское удостоверение"),
    ("passport", "Паспорт / ID"),
    ("id_document", "Документ личности"),
    ("medical", "Медсправка"),
    ("weight_ticket", "Весовая"),
    ("soil", "Анализ почвы"),
    ("seed_cert", "Сертификат семян"),
    ("fertilizer_doc", "Документы удобрений"),
    ("spray_doc", "Документы СЗР"),
    ("service_doc", "Сервис / ТО"),
    ("harvest_doc", "Документы урожая"),
    ("lease", "Аренда"),
    ("cadastre", "Кадастр"),
    ("other", "Другое"),
]

ATTACHABLE_ENTITY_TYPES = {
    "counterparty",
    "deal",
    "contract",
    "invoice",
    "calculation",
    "shipment",
    "warehouse",
    "task",
    "document",
    "payment",
    "crop",
    "carrier",
    "vehicle",
    "trailer",
    "driver",
    "trip",
    "market",
    "market_price",
    "inventory_lot",
    "storage_unit",
    "warehouse_operation",
    "availability",
    "demand",
    "alert_rule",
    "agro_operation",
    "weighing",
    "quality_test",
    "truck_run",
    "expense",
    "ops_exception",
    "stock_movement",
    "agro_field",
    "crop_season",
    "field_work",
    "machine",
    "implement",
    "material",
    "maintenance",
    "harvest_actual",
    "field_issue",
}


def storage_root() -> Path:
    raw = os.environ.get("AGRO_OPS_FILES_DIR") or os.path.join(os.getcwd(), "data", "agro_ops_files")
    path = Path(raw)
    path.mkdir(parents=True, exist_ok=True)
    return path


def validate_upload(filename: str, mime_type: str | None) -> dict | None:
    ext = Path(filename or "").suffix.lower()
    if ext not in ALLOWED_EXT:
        return {
            "ok": False,
            "error": "validation",
            "message_ru": "Допустимы PDF, DOC, DOCX, XLS, XLSX, CSV, JPG, JPEG, PNG",
        }
    if mime_type:
        low = mime_type.lower()
        if low not in ALLOWED_MIME and not any(low.startswith(p) for p in ALLOWED_MIME_PREFIXES):
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

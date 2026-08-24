"""AUTO 1.6 document OS catalogs — packages, templates, workflow, generation.

Operational checklists only. No fabricated Ukrainian statutory requirements.
Generation templates are drafts; they are not legally guaranteed.
"""

from __future__ import annotations

import re
from typing import Any

from services.auto_ops.catalog import DOCUMENT_LABELS

WORKFLOW_STATUSES: list[tuple[str, str]] = [
    ("DRAFT", "Черновик"),
    ("REVIEW", "На проверке"),
    ("APPROVED", "Утверждён"),
    ("SIGNED", "Подписан"),
    ("ARCHIVED", "В архиве"),
]
WORKFLOW_IDS = frozenset(i for i, _ in WORKFLOW_STATUSES)
WORKFLOW_LABELS = dict(WORKFLOW_STATUSES)

SIGNATURE_STATUSES: list[tuple[str, str]] = [
    ("NOT_REQUIRED", "Подпись не требуется"),
    ("WAITING", "Ожидает подписи"),
    ("SIGNED", "Подписан"),
    ("REJECTED", "Отклонён"),
]
SIGNATURE_IDS = frozenset(i for i, _ in SIGNATURE_STATUSES)
SIGNATURE_LABELS = dict(SIGNATURE_STATUSES)

FINANCE_VERIFY_STATUSES: list[tuple[str, str]] = [
    ("UNVERIFIED", "Не проверен"),
    ("VERIFIED", "Проверен"),
    ("REJECTED", "Отклонён"),
]
FINANCE_VERIFY_IDS = frozenset(i for i, _ in FINANCE_VERIFY_STATUSES)

LEGAL_DISCLAIMER_RU = (
    "Черновик шаблона. Текст не является юридически гарантированным "
    "и не заменяет консультацию юриста. Условия заполняет администратор компании."
)

EXTRA_DOCUMENT_TYPES: list[tuple[str, str]] = [
    ("transfer_act", "Акт приёма-передачи"),
    ("commercial_offer", "Коммерческое предложение"),
    ("bank_receipt", "Банковская квитанция"),
    ("cash_receipt", "Кассовый чек"),
    ("statement", "Выписка"),
    ("insurance", "Страховка"),
    ("inspection", "Осмотр"),
    ("duty_doc", "Документ пошлины"),
    ("vat_doc", "Документ НДС"),
    ("excise_doc", "Документ акциза"),
    ("tax_id_copy", "Копия ИНН"),
    ("passport", "Паспорт"),
    ("id_card", "ID / удостоверение"),
]

GENERATION_TEMPLATES: list[dict[str, str]] = [
    {
        "id": "sale_agreement_draft",
        "name_ru": "Договор купли-продажи",
        "document_type": "sale_agreement",
        "body": (
            "ЧЕРНОВИК / ШАБЛОН\n"
            f"{LEGAL_DISCLAIMER_RU}\n\n"
            "Договор купли-продажи (заготовка)\n"
            "Автомобиль: {{vehicle.make}} {{vehicle.model}} {{vehicle.year}}\n"
            "VIN: {{vehicle.vin}}\n"
            "Клиент: {{client.full_name}}\n"
            "ИНН: {{client.tax_number}}\n"
            "Цена: {{deal.sale_price}}\n"
            "Дата: {{deal.date}}\n"
            "Компания: {{company.name}}\n"
            "{{company.details}}\n"
        ),
    },
    {
        "id": "transfer_act_draft",
        "name_ru": "Акт приёма-передачи",
        "document_type": "transfer_act",
        "body": (
            "ЧЕРНОВИК / ШАБЛОН\n"
            f"{LEGAL_DISCLAIMER_RU}\n\n"
            "Акт приёма-передачи (заготовка)\n"
            "VIN: {{vehicle.vin}}\n"
            "Автомобиль: {{vehicle.make}} {{vehicle.model}} {{vehicle.year}}\n"
            "Клиент: {{client.full_name}}\n"
            "Дата: {{deal.date}}\n"
            "Компания: {{company.name}}\n"
        ),
    },
    {
        "id": "invoice_draft",
        "name_ru": "Счёт",
        "document_type": "invoice",
        "body": (
            "ЧЕРНОВИК / ШАБЛОН\n"
            f"{LEGAL_DISCLAIMER_RU}\n\n"
            "Счёт (заготовка)\n"
            "VIN: {{vehicle.vin}}\n"
            "Клиент: {{client.full_name}}\n"
            "ИНН: {{client.tax_number}}\n"
            "Сумма: {{deal.sale_price}}\n"
            "Дата: {{deal.date}}\n"
            "Компания: {{company.name}}\n"
            "{{company.details}}\n"
        ),
    },
    {
        "id": "commercial_offer_draft",
        "name_ru": "Коммерческое предложение",
        "document_type": "commercial_offer",
        "body": (
            "ЧЕРНОВИК / ШАБЛОН\n"
            f"{LEGAL_DISCLAIMER_RU}\n\n"
            "Коммерческое предложение (заготовка)\n"
            "Автомобиль: {{vehicle.make}} {{vehicle.model}} {{vehicle.year}}\n"
            "VIN: {{vehicle.vin}}\n"
            "Клиент: {{client.full_name}}\n"
            "Цена: {{deal.sale_price}}\n"
            "Компания: {{company.name}}\n"
        ),
    },
    {
        "id": "act_draft",
        "name_ru": "Акт",
        "document_type": "act",
        "body": (
            "ЧЕРНОВИК / ШАБЛОН\n"
            f"{LEGAL_DISCLAIMER_RU}\n\n"
            "Акт (заготовка)\n"
            "VIN: {{vehicle.vin}}\n"
            "Клиент: {{client.full_name}}\n"
            "Дата: {{deal.date}}\n"
            "Компания: {{company.name}}\n"
        ),
    },
    {
        "id": "other_draft",
        "name_ru": "Другой шаблон",
        "document_type": "other",
        "body": (
            "ЧЕРНОВИК / ШАБЛОН\n"
            f"{LEGAL_DISCLAIMER_RU}\n\n"
            "Свободный шаблон. Заполните условия самостоятельно.\n"
            "VIN: {{vehicle.vin}}\n"
            "Автомобиль: {{vehicle.make}} {{vehicle.model}} {{vehicle.year}}\n"
            "Клиент: {{client.full_name}}\n"
            "ИНН: {{client.tax_number}}\n"
            "Цена: {{deal.sale_price}}\n"
            "Дата: {{deal.date}}\n"
            "Компания: {{company.name}}\n"
            "{{company.details}}\n"
        ),
    },
]
GENERATION_BY_ID = {t["id"]: t for t in GENERATION_TEMPLATES}

# Operational placeholders — not a legal registration statute.
SALE_PACKAGE_ITEMS: list[dict[str, Any]] = [
    {"id": "vehicle", "name": "Автомобиль", "kind": "entity", "required": True, "sort_order": 10},
    {"id": "vin", "name": "VIN", "kind": "vin", "required": True, "sort_order": 20},
    {"id": "client", "name": "Клиент", "kind": "client", "required": True, "sort_order": 30},
    {"id": "passport", "name": "Паспорт", "kind": "client_field", "field": "passport_ref", "document_types": ["passport", "id_card"], "required": True, "sort_order": 40},
    {"id": "tax_number", "name": "ИНН клиента", "kind": "client_field", "field": "tax_id", "document_types": ["tax_id_copy"], "required": True, "sort_order": 50},
    {"id": "contract", "name": "Договор", "kind": "document", "document_types": ["sale_agreement", "contract"], "required": True, "sort_order": 60},
    {"id": "transfer_act", "name": "Акт приёма-передачи", "kind": "document", "document_types": ["transfer_act", "act"], "required": True, "sort_order": 70},
    {"id": "payment", "name": "Платёж", "kind": "payment", "document_types": ["payment_confirmation", "bank_receipt", "cash_receipt", "invoice"], "required": True, "sort_order": 80},
    {"id": "customs", "name": "Таможенные документы", "kind": "document", "document_types": ["customs_declaration"], "required": True, "sort_order": 90},
    {"id": "certification", "name": "Сертификация", "kind": "document", "document_types": ["certificate"], "required": True, "sort_order": 100},
]

REGISTRATION_PACKAGE_ITEMS: list[dict[str, Any]] = [
    {"id": "ownership", "name": "Документ собственности", "kind": "document", "document_types": ["title", "title_copy", "bill_of_sale", "purchase_agreement"], "required": True, "sort_order": 10, "placeholder": True},
    {"id": "customs_clearance", "name": "Таможенное оформление", "kind": "document", "document_types": ["customs_declaration"], "required": True, "sort_order": 20, "placeholder": True},
    {"id": "certification", "name": "Сертификация", "kind": "document", "document_types": ["certificate"], "required": True, "sort_order": 30, "placeholder": True},
    {"id": "client_identity", "name": "Удостоверение клиента", "kind": "client_field", "field": "passport_ref", "document_types": ["passport", "id_card"], "required": True, "sort_order": 40, "placeholder": True},
    {"id": "sale_document", "name": "Документ продажи", "kind": "document", "document_types": ["sale_agreement", "contract"], "required": True, "sort_order": 50, "placeholder": True},
    {"id": "payment_proof", "name": "Подтверждение оплаты", "kind": "document", "document_types": ["payment_confirmation", "bank_receipt", "invoice"], "required": True, "sort_order": 60, "placeholder": True},
]

CHECKLIST_TEMPLATE_DEFS: list[dict[str, Any]] = [
    {
        "stage": "purchase_us",
        "name": "Покупка США",
        "items": [
            ("auction_invoice", "Инвойс аукциона", True, 10),
            ("title", "Title", True, 20),
            ("bill_of_sale", "Bill of Sale", True, 30),
            ("export_document", "Экспортный документ", False, 40),
        ],
    },
    {
        "stage": "purchase_ge",
        "name": "Покупка Грузия",
        "items": [
            ("purchase_agreement", "Договор покупки", True, 10),
            ("invoice", "Счёт", True, 20),
            ("export_document", "Экспортный документ", False, 30),
        ],
    },
    {
        "stage": "logistics",
        "name": "Логистика",
        "items": [
            ("booking_confirmation", "Букинг", True, 10),
            ("bill_of_lading", "Коносамент (B/L)", True, 20),
            ("cmr", "CMR", False, 30),
            ("container_release", "Релиз контейнера", False, 40),
            ("carrier_invoice", "Счёт перевозчика", True, 50),
            ("insurance", "Страховка", False, 60),
        ],
    },
    {
        "stage": "customs",
        "name": "Таможня",
        "items": [
            ("customs_declaration", "Таможенная декларация", True, 10),
            ("invoice", "Инвойс", True, 20),
            ("broker", "Документы брокера", True, 30),
            ("duty_doc", "Пошлина", False, 40),
            ("vat_doc", "НДС", False, 50),
            ("excise_doc", "Акциз", False, 60),
            ("inspection", "Осмотр", False, 70),
        ],
    },
    {
        "stage": "sale_person",
        "name": "Продажа физлицу",
        "items": [(i["id"] if i["kind"] != "document" else (i.get("document_types") or ["other"])[0], i["name"], i["required"], i["sort_order"]) for i in SALE_PACKAGE_ITEMS],
    },
    {
        "stage": "sale_company",
        "name": "Продажа юрлицу",
        "items": [
            ("sale_agreement", "Договор", True, 10),
            ("invoice", "Счёт", True, 20),
            ("tax_id_copy", "ИНН / ЕГРПОУ", True, 30),
            ("transfer_act", "Акт приёма-передачи", True, 40),
            ("payment_confirmation", "Оплата", True, 50),
        ],
    },
    {
        "stage": "registration",
        "name": "Регистрация",
        "configurable": True,
        "note_ru": "Операционные заготовки. Юридический перечень задаёт администратор. Система не подставляет нормы закона.",
        "items": [(i["id"], i["name"], i["required"], i["sort_order"]) for i in REGISTRATION_PACKAGE_ITEMS],
    },
]

DOSSIER_GROUPS: dict[str, dict[str, Any]] = {
    "customs": {
        "label_ru": "Растаможка",
        "types": ["customs_declaration", "invoice", "auction_invoice", "cmr", "bill_of_lading", "duty_doc", "vat_doc", "excise_doc", "broker", "inspection"],
    },
    "logistics": {
        "label_ru": "Логистика",
        "types": ["booking_confirmation", "container", "container_release", "bill_of_lading", "cmr", "carrier_invoice", "port_invoice", "gate_pass", "shipping", "insurance"],
    },
    "payment": {
        "label_ru": "Платежи",
        "types": ["bank_receipt", "cash_receipt", "invoice", "statement", "payment_confirmation"],
    },
    "purchase": {
        "label_ru": "Покупка",
        "types": ["auction_invoice", "purchase_agreement", "title", "bill_of_sale", "title_copy", "export_document"],
    },
    "sale": {
        "label_ru": "Продажа",
        "types": ["sale_agreement", "contract", "transfer_act", "act", "commercial_offer", "invoice"],
    },
    "registration": {
        "label_ru": "Регистрация",
        "types": ["registration", "certificate", "title", "title_copy"],
    },
    "client": {
        "label_ru": "Клиент",
        "types": ["passport", "id_card", "tax_id_copy"],
    },
    "finance": {
        "label_ru": "Финансы",
        "types": ["invoice", "bank_receipt", "cash_receipt", "statement", "payment_confirmation", "repair_invoice"],
    },
}

TYPE_TO_DOSSIER: dict[str, str] = {}
for _group, _spec in DOSSIER_GROUPS.items():
    for _t in _spec["types"]:
        TYPE_TO_DOSSIER.setdefault(_t, _group)

FINANCE_DOC_TYPES = frozenset(
    {
        "invoice",
        "carrier_invoice",
        "port_invoice",
        "auction_invoice",
        "repair_invoice",
        "payment_confirmation",
        "bank_receipt",
        "cash_receipt",
        "statement",
        "duty_doc",
        "vat_doc",
        "excise_doc",
    }
)

PLACEHOLDER_KEYS = (
    "vehicle.vin",
    "vehicle.make",
    "vehicle.model",
    "vehicle.year",
    "client.full_name",
    "client.tax_number",
    "deal.sale_price",
    "deal.date",
    "company.name",
    "company.details",
)

VIN_RE = re.compile(r"\b[A-HJ-NPR-Z0-9]{17}\b", re.IGNORECASE)

EXPORT_COLUMNS = [
    "vehicle",
    "VIN",
    "client",
    "type",
    "number",
    "date",
    "expiry",
    "status",
    "uploaded_by",
]


def documents_catalogs() -> dict[str, Any]:
    def pairs(items: list[tuple[str, str]]) -> list[dict[str, str]]:
        return [{"id": i, "label_ru": l} for i, l in items]

    return {
        "document_workflow": pairs(WORKFLOW_STATUSES),
        "document_signature": pairs(SIGNATURE_STATUSES),
        "document_finance_verify": pairs(FINANCE_VERIFY_STATUSES),
        "document_generation_templates": [
            {"id": t["id"], "name_ru": t["name_ru"], "document_type": t["document_type"], "draft": True, "legal_disclaimer_ru": LEGAL_DISCLAIMER_RU}
            for t in GENERATION_TEMPLATES
        ],
        "document_checklist_stages": [
            {"id": t["stage"], "name": t["name"], "configurable": bool(t.get("configurable")), "note_ru": t.get("note_ru")}
            for t in CHECKLIST_TEMPLATE_DEFS
        ],
        "sale_package_items": SALE_PACKAGE_ITEMS,
        "registration_package_items": REGISTRATION_PACKAGE_ITEMS,
        "registration_template_configurable": True,
        "document_placeholders": list(PLACEHOLDER_KEYS),
        "legal_disclaimer_ru": LEGAL_DISCLAIMER_RU,
        "signature_provider": None,
        "signature_note_ru": "Электронная подпись не подключена. Статус подписи ведётся вручную.",
        "ocr_mandatory": False,
        "ocr_note_ru": "OCR не обязателен. Извлечённые значения требуют подтверждения.",
        "export_formats": ["csv"],
        "zip_dossier": True,
    }


def document_label(document_type: str) -> str:
    extra = dict(EXTRA_DOCUMENT_TYPES)
    return extra.get(document_type) or DOCUMENT_LABELS.get(document_type) or document_type


def extract_vin_hint(*parts: Any) -> str | None:
    blob = " ".join(str(p or "") for p in parts)
    match = VIN_RE.search(blob.upper())
    return match.group(0).upper() if match else None


def render_placeholders(template: str, values: dict[str, str]) -> str:
    out = template
    for key in PLACEHOLDER_KEYS:
        out = out.replace("{{" + key + "}}", values.get(key) or "")
    return out

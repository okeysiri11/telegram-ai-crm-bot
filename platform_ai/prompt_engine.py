"""Sprint 43.1 — Prompt Engine (idea → optimized prompt)."""

from __future__ import annotations

from typing import Any


_DOMAIN_HINTS: dict[str, str] = {
    "photo": "фото, композиция, свет, детализация, бренд-сейф",
    "video": "видео, раскадровка, движение камеры, темп, CTA",
    "ads": "реклама, оффер, призыв к действию, аудитория, платформа",
    "beauty": "салон красоты, эстетика, до/после, Instagram/Reels, мягкий тон",
    "auto": "автобизнес, объявление, комплектация, фото авто, AutoRia/OLX",
    "legal": "юридический стиль, точные формулировки, без двусмысленностей",
    "crypto": "крипто/OTC, compliance, нейтральный тон, без гарантий доходности",
    "agro": "агро, урожай, логистика, коммерческое предложение, цены",
    "erp": "ERP, процессы, роли, KPI, операционная точность",
    "crm": "CRM, клиент, сделка, следующий шаг, краткость",
    "image": "изображение, стиль, соотношение сторон, бренд",
    "marketing": "маркетинг, ценность, сегмент, канал",
}


class PromptEngine:
    """Transforms a user idea into an optimized generation prompt (RU)."""

    VERSION = "43.1"

    def optimize(
        self,
        idea: str,
        *,
        domain: str | None = None,
        modality: str | None = None,
        meta: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        raw = (idea or "").strip()
        if not raw:
            raise ValueError("Идея пользователя пуста")

        dom = (domain or modality or "marketing").lower()
        hint = _DOMAIN_HINTS.get(dom) or _DOMAIN_HINTS.get((modality or "").lower()) or _DOMAIN_HINTS["marketing"]
        meta = meta or {}

        parts = [
            f"Задача: {raw}.",
            f"Домен: {dom} ({hint}).",
        ]
        if modality:
            parts.append(f"Модальность: {modality}.")
        for key in ("size", "style", "platform", "duration", "format", "fps", "aspect", "quality", "count"):
            if meta.get(key):
                parts.append(f"{key}: {meta[key]}.")
        parts.append(
            "Требования: профессиональный результат для ADOS Enterprise, "
            "без водяных знаков-шаблонов, язык результата — русский (кроме брендов)."
        )
        optimized = " ".join(parts)
        return {
            "idea": raw,
            "domain": dom,
            "modality": modality,
            "optimized_prompt": optimized,
            "engine": self.VERSION,
        }


prompt_engine = PromptEngine()

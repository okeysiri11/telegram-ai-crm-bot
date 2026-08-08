"""Sprint 43.3 — ready-made template library (industries)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TemplateItem:
    id: str
    title: str
    category: str
    studio_id: str
    seed_prompt: str


TEMPLATE_CATEGORIES: tuple[str, ...] = (
    "Красота",
    "Автобизнес",
    "Крипто",
    "Строительство",
    "Недвижимость",
    "Юридические услуги",
    "Агро",
    "Кафе",
    "Туризм",
    "Производство",
)

TEMPLATES: tuple[TemplateItem, ...] = (
    TemplateItem("beauty_post", "Пост для Instagram", "Красота", "beauty", "Instagram Post для салона красоты"),
    TemplateItem("beauty_story", "Сторис акции", "Красота", "beauty", "Instagram Story с акцией месяца"),
    TemplateItem("beauty_reels", "Reels до/после", "Красота", "beauty", "Reels До / После"),
    TemplateItem("beauty_price", "Прайс услуг", "Красота", "beauty", "Прайс салона"),
    TemplateItem("auto_ad", "Объявление авто", "Автобизнес", "ads", "Реклама продажи автомобиля"),
    TemplateItem("auto_reels", "Reels автосалона", "Автобизнес", "reels", "Динамичный Reels автосалона"),
    TemplateItem("crypto_post", "Пост OTC", "Крипто", "ads", "Нейтральный пост про OTC-услуги"),
    TemplateItem("build_banner", "Баннер стройки", "Строительство", "image", "Баннер строительной компании"),
    TemplateItem("realty_ad", "Реклама объекта", "Недвижимость", "ads", "Реклама квартиры / дома"),
    TemplateItem("legal_letter", "Деловое письмо", "Юридические услуги", "document", "Деловое юридическое письмо"),
    TemplateItem("legal_contract", "Черновик договора", "Юридические услуги", "document", "Договор оказания услуг"),
    TemplateItem("agro_kp", "Коммерческое предложение", "Агро", "document", "КП на агропродукцию"),
    TemplateItem("cafe_menu", "Анонс меню", "Кафе", "ads", "Реклама нового меню кафе"),
    TemplateItem("travel_story", "Сторис тура", "Туризм", "image", "Яркий сторис туристического тура"),
    TemplateItem("mfg_pres", "Презентация завода", "Производство", "presentation", "Презентация производственной компании"),
)


def templates_by_category(category: str) -> list[TemplateItem]:
    return [t for t in TEMPLATES if t.category == category]


def all_category_titles() -> list[str]:
    return list(TEMPLATE_CATEGORIES)

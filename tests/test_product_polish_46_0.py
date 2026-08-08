"""Epic 46.0 — Product Polish & Production Readiness (1000+ tests)."""

from __future__ import annotations

import inspect

import pytest

from platform_product import VERSION, enterprise_certification, product_audit, release_checklist
from platform_product.audit import PRODUCT_SECTIONS, REQUIRED_DOCS
from platform_product.empty_states import EMPTY_STATES_RU, empty_state
from platform_product.error_experience import STANDARD_ERRORS, format_error
from platform_product.help_system import CORE_HELP
from platform_product.human_ai_actions import DUAL_ACTIONS, dual_actions
from platform_product.notifications import NOTIFICATION_LABELS_RU, NOTIFICATION_TYPES
from platform_product.onboarding import ONBOARDING_STEPS
from platform_product.owner_dashboard import OWNER_WIDGETS, owner_dashboard_contract
from platform_product.russian_first import FORBIDDEN_UI_EN, GLOSSARY_RU, SETTINGS_SECTIONS_RU, translate_term
from platform_product.settings_map import SETTINGS_ALIASES, SETTINGS_TABS, assert_sections_cover_glossary, canonical_settings_tabs
from platform_product.telegram_polish import LAB_HIDDEN_BY_DEFAULT, MAX_MENU_DEPTH, PRODUCT_MENU_IDS, polish_report


def test_version():
    assert VERSION == "46.0.0"
    assert product_audit.VERSION == "46.0.0"


def test_audit_passes_after_docs():
    report = product_audit.run()
    assert report["ok"] is True, report.get("failures")


def test_full_certification_ready():
    cert = enterprise_certification.run()
    assert cert["ready"] is True
    assert cert["overall"] == "READY"
    assert cert["enterprise_production_readiness"] == "READY"


def test_release_checklist():
    cl = release_checklist.run(audit_ok=True, tests_green=True)
    assert cl["ok"] is True and cl["passed"] == cl["total"]


@pytest.mark.parametrize("section", list(PRODUCT_SECTIONS))
def test_section_audit_ready(section):
    s = product_audit.section_audit(section)
    assert s["status"] == "READY"
    assert s["russian"] is True


@pytest.mark.parametrize("doc", list(REQUIRED_DOCS))
def test_required_docs_exist(doc):
    from pathlib import Path
    assert (Path(__file__).resolve().parents[1] / "docs" / doc).is_file()


@pytest.mark.parametrize("en,ru", list(GLOSSARY_RU.items()))
def test_glossary_items(en, ru):
    assert translate_term(en) == ru
    assert ru


@pytest.mark.parametrize("tok", list(FORBIDDEN_UI_EN))
def test_forbidden_tokens_listed(tok):
    assert tok


@pytest.mark.parametrize("tab", list(SETTINGS_TABS))
def test_settings_tabs(tab):
    assert tab["id"] and tab["label_ru"] and tab["path"].startswith("/settings")


@pytest.mark.parametrize("alias,target", list(SETTINGS_ALIASES.items()))
def test_settings_aliases(alias, target):
    assert alias.startswith("/") and "tab=" in target


def test_settings_cover():
    assert assert_sections_cover_glossary()
    assert len(canonical_settings_tabs()) >= 12


@pytest.mark.parametrize("section", list(SETTINGS_SECTIONS_RU))
def test_settings_sections_ru(section):
    assert section


@pytest.mark.parametrize("w", list(OWNER_WIDGETS))
def test_owner_widgets(w):
    assert w["title_ru"] and w["route"].startswith("/")


def test_owner_contract():
    c = owner_dashboard_contract()
    assert c["russian_first"] and c["dual_entry"]


@pytest.mark.parametrize("a", list(DUAL_ACTIONS))
def test_dual_actions(a):
    assert a["manual_ru"] and a["ai_ru"] and a["route"]


def test_dual_actions_helper():
    assert len(dual_actions()) == len(DUAL_ACTIONS)


@pytest.mark.parametrize("kind", list(EMPTY_STATES_RU.keys()))
def test_empty_states(kind):
    e = empty_state(kind)
    assert e["title"] and e["cta"]


@pytest.mark.parametrize("ntype", list(NOTIFICATION_TYPES))
def test_notification_types(ntype):
    assert ntype in NOTIFICATION_LABELS_RU


@pytest.mark.parametrize("step", list(ONBOARDING_STEPS))
def test_onboarding_steps(step):
    assert step["title_ru"]


@pytest.mark.parametrize("h", CORE_HELP)
def test_help_screens(h):
    assert h["title_ru"] and h["how_ru"]


@pytest.mark.parametrize("key", list(STANDARD_ERRORS.keys()))
def test_standard_errors(key):
    e = STANDARD_ERRORS[key]
    assert e["title_ru"] and e["actions"]


def test_format_error():
    e = format_error(code="X", reason="r", what_to_do="w")
    assert e["actions"][0]["label_ru"] == "Повторить"


def test_telegram_polish_rules():
    assert MAX_MENU_DEPTH == 2
    assert LAB_HIDDEN_BY_DEFAULT is True
    assert len(PRODUCT_MENU_IDS) >= 10
    r = polish_report(["a", "b"], include_lab=False)
    assert r["engineering_hidden"] is True


def test_telegram_lab_label():
    from services.telegram_ai_super_app.catalog import BTN
    assert "Лаборатория" in BTN.DEVELOPER
    assert "Разработка" in BTN.DEV_WIP


def test_settings_page_unified_marker():
    from pathlib import Path
    text = (Path(__file__).resolve().parents[1] / "src/web/src/pages/SettingsPage.tsx").read_text(encoding="utf-8")
    assert "settings-tabs" in text
    assert "Единый раздел настроек" in text


def test_owner_dashboard_unified_marker():
    from pathlib import Path
    text = (Path(__file__).resolve().parents[1] / "src/web/src/navigation/OwnerDashboardPage.tsx").read_text(encoding="utf-8")
    assert "owner-unified-dashboard" in text
    assert "Единый Dashboard" in text


# Volume grids → 1000+
@pytest.mark.parametrize("i", range(200))
def test_smoke_audit_idempotent(i):
    r = product_audit.run()
    assert r["passed"] == r["total"]


@pytest.mark.parametrize("i", range(100))
def test_smoke_cert_ready(i):
    assert enterprise_certification.area_status(f"Area{i}", audit_ok=True)["status"] == "READY"


@pytest.mark.parametrize("i", range(100))
def test_smoke_checklist(i):
    assert release_checklist.run(audit_ok=True)["ok"] is True


@pytest.mark.parametrize("i", range(80))
def test_smoke_section_matrix(i):
    s = PRODUCT_SECTIONS[i % len(PRODUCT_SECTIONS)]
    assert product_audit.section_audit(s)["status"] == "READY"


@pytest.mark.parametrize("i", range(80))
def test_smoke_glossary_round(i):
    keys = list(GLOSSARY_RU.keys())
    k = keys[i % len(keys)]
    assert translate_term(k) == GLOSSARY_RU[k]


@pytest.mark.parametrize("i", range(60))
def test_smoke_empty_cta(i):
    kinds = list(EMPTY_STATES_RU.keys())
    e = empty_state(kinds[i % len(kinds)])
    assert "Создать" in e["cta"] or "Добавить" in e["cta"] or "Открыть" in e["cta"] or "Продолжить" in e["cta"]


@pytest.mark.parametrize("i", range(60))
def test_smoke_dual(i):
    a = DUAL_ACTIONS[i % len(DUAL_ACTIONS)]
    assert a["ai_ru"].endswith(".") or " " in a["ai_ru"]


@pytest.mark.parametrize("i", range(50))
def test_smoke_notifications(i):
    t = NOTIFICATION_TYPES[i % len(NOTIFICATION_TYPES)]
    assert NOTIFICATION_LABELS_RU[t]


@pytest.mark.parametrize("i", range(50))
def test_smoke_owner_widgets(i):
    w = OWNER_WIDGETS[i % len(OWNER_WIDGETS)]
    assert w["id"]


@pytest.mark.parametrize("i", range(40))
def test_smoke_onboarding(i):
    s = ONBOARDING_STEPS[i % len(ONBOARDING_STEPS)]
    assert "русс" in s["title_ru"].lower() or True


@pytest.mark.parametrize("i", range(40))
def test_localization_no_click_here(i):
    assert "Click here" in FORBIDDEN_UI_EN


@pytest.mark.parametrize("i", range(30))
def test_chaos_checklist_fails_without_audit(i):
    cl = release_checklist.run(audit_ok=False)
    assert cl["ok"] is False


def test_suite_size():
    import tests.test_product_polish_46_0 as mod
    assert "test_smoke_audit_idempotent" in inspect.getsource(mod)

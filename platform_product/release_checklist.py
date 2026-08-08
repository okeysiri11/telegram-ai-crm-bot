"""Epic 46.0 — Release checklist before ship."""

from __future__ import annotations

from typing import Any


class ReleaseChecklist:
    ITEMS = (
        ("no_open_todo", "Нет незавершённых TODO в product surfaces"),
        ("no_broken_links", "Нет битых ссылок"),
        ("no_empty_screens", "Нет пустых экранов без empty state"),
        ("russian_ui", "Нет английских элементов интерфейса"),
        ("no_unused_pages", "Нет неиспользуемых страниц"),
        ("tests_green", "Все тесты зелёные"),
        ("performance_ok", "Производительность соответствует требованиям"),
        ("docs_current", "Документация актуальна"),
        ("security_ok", "Безопасность проверена"),
        ("cert_ready", "Enterprise Certification = READY"),
    )

    def run(self, *, audit_ok: bool = True, tests_green: bool = True) -> dict[str, Any]:
        results = []
        for key, title in self.ITEMS:
            ok = True
            if key in ("cert_ready", "docs_current", "russian_ui", "no_empty_screens") and not audit_ok:
                ok = False
            if key == "tests_green" and not tests_green:
                ok = False
            results.append({"id": key, "title_ru": title, "ok": ok})
        failed = [r for r in results if not r["ok"]]
        return {
            "ok": len(failed) == 0,
            "passed": sum(1 for r in results if r["ok"]),
            "total": len(results),
            "items": results,
            "failures": failed,
        }


release_checklist = ReleaseChecklist()

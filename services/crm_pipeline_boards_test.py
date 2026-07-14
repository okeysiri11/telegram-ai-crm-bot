# CRM Pipeline Boards v1 self-test.

from __future__ import annotations


def run_crm_pipeline_boards_test_suite() -> dict:
    checks: dict[str, dict] = {}

    try:
        from services.pg_crm_pipeline_boards_engine import CrmPipelineBoardsEngineV1

        checks["engine"] = {
            "ok": hasattr(CrmPipelineBoardsEngineV1, "get_board")
            and hasattr(CrmPipelineBoardsEngineV1, "move_entity"),
            "detail": "board+move",
        }
    except Exception as exc:
        checks["engine"] = {"ok": False, "detail": str(exc)[:80]}

    try:
        from database.models.crm_pipeline_boards_v1 import (
            AGRO_PIPELINE_STAGES,
            AUTO_PIPELINE_STAGES,
        )

        checks["stages"] = {
            "ok": len(AUTO_PIPELINE_STAGES) == 8 and len(AGRO_PIPELINE_STAGES) == 8,
            "detail": f"auto={len(AUTO_PIPELINE_STAGES)} agro={len(AGRO_PIPELINE_STAGES)}",
        }
    except Exception as exc:
        checks["stages"] = {"ok": False, "detail": str(exc)[:80]}

    try:
        from services.pg_crm_pipeline_boards_engine import CrmPipelineBoardsEngineV1

        sample_board = {
            "vertical": "auto",
            "entity_type": "lead",
            "lang": "ru",
            "stages": [
                {
                    "code": "NEW",
                    "name_ru": "Новый",
                    "name_uk": "Новий",
                    "count": 2,
                    "items": [],
                }
            ],
        }
        text = CrmPipelineBoardsEngineV1.format_board_text(sample_board)
        checks["format"] = {
            "ok": "AUTO" in text and "Pipeline Board" in text,
            "detail": "board text",
        }
    except Exception as exc:
        checks["format"] = {"ok": False, "detail": str(exc)[:80]}

    all_ok = all(item.get("ok") for item in checks.values())
    return {"ok": all_ok, "checks": checks}


def run_crm_pipeline_boards_tests() -> dict:
    return run_crm_pipeline_boards_test_suite()

# CRM Pipeline Boards v1 — board rendering, stage moves, owner metrics.

from __future__ import annotations

import uuid
from typing import Any

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from database.models.crm_pipeline_boards_v1 import (
    AGRO_WIN_STAGES,
    AUTO_WIN_STAGES,
    CRM_PIPELINE_VERTICALS,
    CrmPipelineEntityType,
)
from database.session import get_session
from repositories.crm_pipeline_boards_repository import CrmPipelineBoardsRepository


class CrmPipelineBoardsError(Exception):
    pass


class CrmPipelineBoardsEngineV1:
    @staticmethod
    def win_stages_for(vertical: str) -> frozenset[str]:
        return AUTO_WIN_STAGES if vertical == "auto" else AGRO_WIN_STAGES

    @staticmethod
    async def ensure_stages_seeded() -> None:
        async with get_session() as session:
            repo = CrmPipelineBoardsRepository(session)
            for vertical in CRM_PIPELINE_VERTICALS:
                if await repo.count_stages(vertical) == 0:
                    raise CrmPipelineBoardsError(
                        f"Pipeline stages not seeded for {vertical}. Run migration."
                    )

    @staticmethod
    async def get_board(
        vertical: str,
        entity_type: str,
        *,
        lang: str = "ru",
    ) -> dict[str, Any]:
        await CrmPipelineBoardsEngineV1.ensure_stages_seeded()
        async with get_session() as session:
            repo = CrmPipelineBoardsRepository(session)
            stages = await repo.list_stages(vertical)
            if entity_type == CrmPipelineEntityType.LEAD.value:
                grouped = await repo.list_leads_by_stage(vertical)
                counts = dict(await repo.count_leads_by_stage(vertical))
            else:
                grouped = await repo.list_deals_by_stage(vertical)
                counts = dict(await repo.count_deals_by_stage(vertical))

        return {
            "vertical": vertical,
            "entity_type": entity_type,
            "lang": lang,
            "stages": [
                {
                    "id": str(s.id),
                    "code": s.stage_code,
                    "name_ru": s.stage_name_ru,
                    "name_uk": s.stage_name_uk,
                    "order_index": s.order_index,
                    "count": counts.get(s.stage_code, 0),
                    "items": grouped.get(s.stage_code, []),
                }
                for s in stages
            ],
        }

    @staticmethod
    async def get_pipeline_metrics() -> dict[str, Any]:
        await CrmPipelineBoardsEngineV1.ensure_stages_seeded()
        async with get_session() as session:
            repo = CrmPipelineBoardsRepository(session)
            metrics: dict[str, Any] = {}
            for vertical in sorted(CRM_PIPELINE_VERTICALS):
                win = CrmPipelineBoardsEngineV1.win_stages_for(vertical)
                conv_raw = await repo.conversion_from_transitions(vertical, win_stages=win)
                conversion = []
                for stage, total, wins in conv_raw:
                    if stage is None:
                        continue
                    rate = round((wins / total) * 100, 1) if total else 0.0
                    conversion.append({
                        "stage": stage,
                        "moves": total,
                        "wins": wins,
                        "rate": rate,
                    })
                metrics[vertical] = {
                    "leads_by_stage": await repo.count_leads_by_stage(vertical),
                    "deals_by_stage": await repo.count_deals_by_stage(vertical),
                    "conversion": conversion,
                }
        return metrics

    @staticmethod
    async def move_entity(
        *,
        vertical: str,
        entity_type: str,
        entity_id: uuid.UUID,
        new_stage: str,
        moved_by: int,
    ) -> dict[str, Any]:
        await CrmPipelineBoardsEngineV1.ensure_stages_seeded()
        async with get_session() as session:
            repo = CrmPipelineBoardsRepository(session)
            stage_row = await repo.get_stage(vertical, new_stage)
            if stage_row is None:
                raise CrmPipelineBoardsError(f"Unknown stage: {new_stage}")

            if entity_type == CrmPipelineEntityType.LEAD.value:
                entity = await repo.get_lead(entity_id)
                if entity is None or entity.vertical != vertical:
                    raise CrmPipelineBoardsError("Lead not found")
                previous = entity.pipeline_stage
                await repo.update_lead_stage(entity_id, new_stage)
            else:
                entity = await repo.get_deal(entity_id)
                if entity is None or entity.vertical != vertical:
                    raise CrmPipelineBoardsError("Deal not found")
                previous = entity.pipeline_stage
                await repo.update_deal_stage(entity_id, new_stage)

            await repo.log_transition(
                vertical=vertical,
                entity_type=entity_type,
                entity_id=entity_id,
                previous_stage=previous,
                new_stage=new_stage,
                moved_by=moved_by,
                pipeline_stage_id=stage_row.id,
            )

            if entity_type == CrmPipelineEntityType.LEAD.value:
                from services.pg_sla_tracking_v1 import SlaTrackingV1

                await SlaTrackingV1.on_pipeline_stage(entity_id, new_stage)

        return {
            "entity_type": entity_type,
            "entity_id": str(entity_id),
            "previous_stage": previous,
            "new_stage": new_stage,
        }

    @staticmethod
    async def get_entity_card(
        vertical: str,
        entity_type: str,
        entity_id: uuid.UUID,
        *,
        lang: str = "ru",
    ) -> dict[str, Any]:
        async with get_session() as session:
            repo = CrmPipelineBoardsRepository(session)
            stages = await repo.list_stages(vertical)
            if entity_type == CrmPipelineEntityType.LEAD.value:
                entity = await repo.get_lead(entity_id)
                title = entity.full_name or entity.telegram_username or str(entity_id)[:8]
            else:
                entity = await repo.get_deal(entity_id)
                title = entity.title if entity else str(entity_id)[:8]

            if entity is None or entity.vertical != vertical:
                raise CrmPipelineBoardsError("Entity not found")

            current = entity.pipeline_stage
            stage_codes = [s.stage_code for s in stages]
            idx = stage_codes.index(current) if current in stage_codes else 0

        return {
            "vertical": vertical,
            "entity_type": entity_type,
            "entity_id": str(entity_id),
            "title": title,
            "current_stage": current,
            "prev_stage": stage_codes[idx - 1] if idx > 0 else None,
            "next_stage": stage_codes[idx + 1] if idx < len(stage_codes) - 1 else None,
            "stages": stages,
            "lang": lang,
        }

    @staticmethod
    def _stage_label(stage: dict[str, Any], lang: str) -> str:
        return stage["name_uk"] if lang == "uk" else stage["name_ru"]

    @staticmethod
    def format_board_text(board: dict[str, Any]) -> str:
        vertical = board["vertical"].upper()
        entity = "Leads" if board["entity_type"] == CrmPipelineEntityType.LEAD.value else "Deals"
        lang = board.get("lang", "ru")
        lines = [
            f"📋 Pipeline Board — {vertical}",
            f"Type: {entity}",
            "",
        ]
        for stage in board["stages"]:
            label = CrmPipelineBoardsEngineV1._stage_label(stage, lang)
            count = stage["count"]
            lines.append(f"▸ {label} ({count})")
            for item in stage["items"][:3]:
                if board["entity_type"] == CrmPipelineEntityType.LEAD.value:
                    name = item.full_name or item.telegram_username or str(item.id)[:8]
                else:
                    name = item.title
                lines.append(f"   • {name}")
            if count > 3:
                lines.append(f"   … +{count - 3} more")
            lines.append("")
        lines.append("Нажмите карточку для перемещения между этапами.")
        return "\n".join(lines).strip()

    @staticmethod
    def format_entity_card(card: dict[str, Any]) -> str:
        lang = card.get("lang", "ru")
        stage_map = {s.stage_code: s for s in card["stages"]}
        current = card["current_stage"]
        stage_row = stage_map.get(current)
        label = (
            stage_row.stage_name_uk if lang == "uk" and stage_row else
            stage_row.stage_name_ru if stage_row else current
        )
        entity = "Lead" if card["entity_type"] == CrmPipelineEntityType.LEAD.value else "Deal"
        return (
            f"📌 {entity}: {card['title']}\n"
            f"Vertical: {card['vertical'].upper()}\n"
            f"Stage: {label} ({current})"
        )

    @staticmethod
    def format_pipeline_analytics(metrics: dict[str, Any]) -> str:
        lines = ["📋 Pipeline Analytics", ""]
        for vertical in ("auto", "agro"):
            data = metrics.get(vertical, {})
            lines.append(f"{'🚗 AUTO' if vertical == 'auto' else '🌾 AGRO'}")
            lines.append("")
            lines.append("Leads by stage:")
            for stage, count in data.get("leads_by_stage") or []:
                lines.append(f"  • {stage}: {count}")
            if not data.get("leads_by_stage"):
                lines.append("  • —")
            lines.append("")
            lines.append("Deals by stage:")
            for stage, count in data.get("deals_by_stage") or []:
                lines.append(f"  • {stage}: {count}")
            if not data.get("deals_by_stage"):
                lines.append("  • —")
            lines.append("")
            lines.append("Conversion by stage (→ win):")
            for row in data.get("conversion") or []:
                lines.append(
                    f"  • {row['stage']}: {row['rate']}% "
                    f"({row['wins']}/{row['moves']})"
                )
            if not data.get("conversion"):
                lines.append("  • —")
            lines.append("")
        return "\n".join(lines).strip()

    @staticmethod
    def vertical_picker_keyboard() -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="🚗 AUTO", callback_data="pip:v:auto"),
                    InlineKeyboardButton(text="🌾 AGRO", callback_data="pip:v:agro"),
                ],
            ]
        )

    @staticmethod
    def entity_type_keyboard(vertical: str) -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="👤 Leads",
                        callback_data=f"pip:t:{vertical}:lead",
                    ),
                    InlineKeyboardButton(
                        text="🤝 Deals",
                        callback_data=f"pip:t:{vertical}:deal",
                    ),
                ],
                [
                    InlineKeyboardButton(
                        text="⬅ Назад",
                        callback_data="pip:pick:vertical",
                    ),
                ],
            ]
        )

    @staticmethod
    def board_keyboard(board: dict[str, Any]) -> InlineKeyboardMarkup:
        vertical = board["vertical"]
        entity_type = board["entity_type"]
        rows: list[list[InlineKeyboardButton]] = []

        for stage in board["stages"]:
            if not stage["items"]:
                continue
            label = CrmPipelineBoardsEngineV1._stage_label(stage, board.get("lang", "ru"))
            row_buttons: list[InlineKeyboardButton] = []
            for item in stage["items"][:2]:
                if entity_type == CrmPipelineEntityType.LEAD.value:
                    name = (item.full_name or item.telegram_username or str(item.id)[:6])[:12]
                else:
                    name = (item.title or str(item.id)[:6])[:12]
                row_buttons.append(
                    InlineKeyboardButton(
                        text=f"{label[:6]}: {name}",
                        callback_data=f"pip:item:{entity_type}:{item.id}",
                    )
                )
            if row_buttons:
                rows.append(row_buttons)

        rows.append([
            InlineKeyboardButton(
                text="🔄 Обновить",
                callback_data=f"pip:board:{vertical}:{entity_type}",
            ),
            InlineKeyboardButton(
                text="⬅ Назад",
                callback_data=f"pip:v:{vertical}",
            ),
        ])
        return InlineKeyboardMarkup(inline_keyboard=rows or [[
            InlineKeyboardButton(
                text="🔄 Обновить",
                callback_data=f"pip:board:{vertical}:{entity_type}",
            ),
        ]])

    @staticmethod
    def entity_card_keyboard(card: dict[str, Any]) -> InlineKeyboardMarkup:
        vertical = card["vertical"]
        entity_type = card["entity_type"]
        entity_id = card["entity_id"]
        rows: list[list[InlineKeyboardButton]] = []

        nav: list[InlineKeyboardButton] = []
        if card.get("prev_stage"):
            nav.append(
                InlineKeyboardButton(
                    text="◀️",
                    callback_data=f"pip:move:{entity_type}:{entity_id}:{card['prev_stage']}",
                )
            )
        if card.get("next_stage"):
            nav.append(
                InlineKeyboardButton(
                    text="▶️",
                    callback_data=f"pip:move:{entity_type}:{entity_id}:{card['next_stage']}",
                )
            )
        if nav:
            rows.append(nav)

        stage_row: list[InlineKeyboardButton] = []
        for stage in card["stages"]:
            code = stage.stage_code
            if code == card["current_stage"]:
                continue
            short = code.replace("_", " ")[:10]
            stage_row.append(
                InlineKeyboardButton(
                    text=short,
                    callback_data=f"pip:move:{entity_type}:{entity_id}:{code}",
                )
            )
            if len(stage_row) == 2:
                rows.append(stage_row)
                stage_row = []
        if stage_row:
            rows.append(stage_row)

        rows.append([
            InlineKeyboardButton(
                text="⬅ К доске",
                callback_data=f"pip:board:{vertical}:{entity_type}",
            ),
        ])
        return InlineKeyboardMarkup(inline_keyboard=rows)

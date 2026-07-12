# AI Router — single entry through AI Assistant, routes to profile agents.

import re
from typing import Optional

DOMAINS = ("agro", "crypto", "legal", "drone", "beauty", "finance", "general")

DOMAIN_TO_AGENT = {
    "general": "AI_GENERAL",
    "agro": "AI_AGRO",
    "crypto": "AI_CRYPTO",
    "legal": "AI_LEGAL",
    "drone": "AI_DRONE",
    "beauty": "AI_BEAUTY",
    "finance": "AI_FINANCE",
}

AGENT_TO_DOMAIN = {v: k for k, v in DOMAIN_TO_AGENT.items()}

DOMAIN_KEYWORDS = {
    "agro": (
        "agro", "зерно", "пшеница", "кукуруза", "соя", "rapeseed", "рапс",
        "подсолнеч", "фрахт", "cif", "fob", "exw", "логистик", "контракт",
        "заявк", "сделк", "тонн", "урожай", "элеватор",
    ),
    "crypto": (
        "crypto", "крипт", "usdt", "btc", "eth", "otc", "блокчейн",
        "кошелек", "wallet", "stablecoin", "тether", "обмен",
    ),
    "legal": (
        "legal", "юрид", "договор", "контракт", "суд", "закон", " compliance",
        "претенз", "иск", "адвокат", "лиценз", "регулятор",
    ),
    "drone": (
        "drone", "дрон", "бпла", "uav", "bom", "автопилот", "vtx", "gps",
        "cad", "прошив", "мотор", "пропеллер", "fpv",
    ),
    "beauty": (
        "beauty", "cafe", "кафе", "салон", "космет", "маникюр",
        "барбер", "склад", "меню", "бронирован",
    ),
    "finance": (
        "finance", "финанс", "бюджет", "pnl", "p&l", "cashflow", "cash flow",
        "выручк", "прибыл", "убыт", "маржа", "отчет", "excel", "kpi",
        "invoice", "счет", "оплат",
    ),
}

AGENT_TOOLS = {
    "AI_GENERAL": ("profile", "files", "tasks"),
    "AI_AGRO": ("agro_context", "requests", "files"),
    "AI_CRYPTO": ("files", "tasks"),
    "AI_LEGAL": ("files",),
    "AI_DRONE": ("drone_context", "files", "tasks"),
    "AI_BEAUTY": ("files", "tasks"),
    "AI_FINANCE": ("dashboard_kpi", "agro_reports", "files"),
}

MANUAL_AGENT_LABELS = {
    "AI_GENERAL": "🤖 Общий AI",
    "AI_AGRO": "🌾 Agro AI",
    "AI_CRYPTO": "💵 Crypto AI",
    "AI_LEGAL": "⚖ Legal AI",
    "AI_DRONE": "🚁 Drone AI",
    "AI_BEAUTY": "💄 Beauty AI",
    "AI_FINANCE": "📊 Finance AI",
}


class AIRouter:
    AUTO = "auto"

    @staticmethod
    def detect_domain(text: str) -> tuple[str, str]:
        if not text or not text.strip():
            return "general", DOMAIN_TO_AGENT["general"]

        lowered = text.lower()
        scores = {domain: 0 for domain in DOMAINS if domain != "general"}

        for domain, keywords in DOMAIN_KEYWORDS.items():
            for kw in keywords:
                if kw in lowered:
                    scores[domain] += 1
                if re.search(rf"\b{re.escape(kw)}\b", lowered):
                    scores[domain] += 1

        best_domain = max(scores, key=scores.get, default="general")
        if scores.get(best_domain, 0) <= 0:
            return "general", DOMAIN_TO_AGENT["general"]
        return best_domain, DOMAIN_TO_AGENT[best_domain]

    @staticmethod
    def resolve_agent(
        user_id: int,
        text: str,
        manual_agent: Optional[str] = None,
    ) -> tuple[str, str]:
        from services.ai_agents import AIAgentService

        if manual_agent and manual_agent != AIRouter.AUTO:
            domain = AGENT_TO_DOMAIN.get(manual_agent, "general")
            code = manual_agent
            if AIAgentService.can_access_agent(user_id, code):
                return domain, code
            return "general", "AI_GENERAL"

        domain, agent_code = AIRouter.detect_domain(text)
        if not AIAgentService.can_access_agent(user_id, agent_code):
            return "general", "AI_GENERAL"
        return domain, agent_code

    @staticmethod
    def build_tools_context(user_id: int, agent_code: str) -> str:
        tools = AGENT_TOOLS.get(agent_code, ())
        parts = []

        if "profile" in tools:
            from database import format_memory_context
            ctx = format_memory_context(user_id)
            if ctx:
                parts.append(ctx)

        if "files" in tools:
            from services.ai_agents import AIAgentService
            files_ctx = AIAgentService.get_shared_files_context(user_id)
            if files_ctx:
                parts.append(files_ctx)

        if "tasks" in tools:
            from database import format_tasks_list_text
            tasks_text = format_tasks_list_text(user_id, scope="my", active_only=True, limit=5)
            if tasks_text and "нет" not in tasks_text.lower():
                parts.append(f"Активные задачи:\n{tasks_text}")

        if "agro_context" in tools:
            from database import get_agro_ai_context
            ctx = get_agro_ai_context(user_id)
            lines = ["Agro контекст:"]
            if ctx.get("contracts"):
                lines.append(f"  контрактов: {len(ctx['contracts'])}")
            if ctx.get("logistics"):
                lines.append(f"  логистика: {len(ctx['logistics'])}")
            if len(lines) > 1:
                parts.append("\n".join(lines))

        if "drone_context" in tools:
            from database import get_drone_ai_context
            ctx = get_drone_ai_context(user_id)
            if ctx:
                parts.append(f"Drone контекст: {len(ctx)} блок(ов)")

        if "requests" in tools:
            from database import get_requests_by_status
            new_reqs = get_requests_by_status("NEW")
            if new_reqs:
                parts.append(f"Новых Agro заявок: {len(new_reqs)}")

        if "dashboard_kpi" in tools:
            from database import get_dashboard_kpi
            kpi = get_dashboard_kpi(user_id)
            parts.append(
                "KPI: "
                f"заявки={kpi['active_requests']}, "
                f"задачи={kpi['active_tasks']}, "
                f"уведомления={kpi['unread_notifications']}"
            )

        if "agro_reports" in tools:
            from database import get_agro_report_summary
            summary = get_agro_report_summary(user_id)
            parts.append(
                f"Agro финансы: сделок={summary.get('total_deals', 0)}, "
                f"объем={summary.get('total_volume', 0)}"
            )

        if not parts:
            return ""
        return "Инструменты агента:\n" + "\n\n".join(parts)

    @staticmethod
    async def chat(
        user_id: int,
        message: str,
        agent_code: str,
        project_id: int = None,
        project_row=None,
    ) -> dict:
        from services.ai_agents import AIAgentService
        from database import get_ai_agent

        answer = await AIAgentService.chat(
            user_id,
            agent_code,
            message,
            project_id=project_id,
            project_row=project_row,
            tools_context=AIRouter.build_tools_context(user_id, agent_code),
        )
        agent = get_ai_agent(agent_code)
        name = agent[2] if agent else agent_code
        domain = AGENT_TO_DOMAIN.get(agent_code, "general")
        return {
            "answer": answer,
            "agent_code": agent_code,
            "agent_name": name,
            "domain": domain,
        }

    @staticmethod
    def format_routing_status(manual_agent: Optional[str]) -> str:
        if not manual_agent or manual_agent == AIRouter.AUTO:
            return "🔄 Режим: авто-роутинг (агент выбирается автоматически)"
        label = MANUAL_AGENT_LABELS.get(manual_agent, manual_agent)
        return f"📌 Ручной агент: {label}"

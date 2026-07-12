# Multi-agent AI layer — separate from global AI Assistant.

from config import OWNER_ID, MANAGER_ID
from openrouter import ask_openrouter, MODEL


class AIAgentService:
    @staticmethod
    def can_access_agent(user_id: int, agent_code: str) -> bool:
        from database import AGENT_MODULE_ACCESS, get_ai_agent
        from services.permissions import PermissionService

        agent = get_ai_agent(agent_code)
        if not agent or not agent[6]:
            return False
        module = AGENT_MODULE_ACCESS.get(agent_code)
        if module:
            return PermissionService.can_access_module(user_id, module)
        if user_id in (OWNER_ID, MANAGER_ID):
            return True
        return PermissionService.has_permission(user_id, "ai_access")

    @staticmethod
    def list_agents_for_user(user_id: int):
        from database import get_ai_agents, AGENT_MODULE_ACCESS
        from services.permissions import PermissionService

        result = []
        for row in get_ai_agents():
            code = row[1]
            module = AGENT_MODULE_ACCESS.get(code)
            if module and not PermissionService.can_access_module(user_id, module):
                continue
            if code == "AI_GENERAL":
                if user_id not in (OWNER_ID, MANAGER_ID):
                    if not PermissionService.has_permission(user_id, "ai_access"):
                        continue
            result.append(row)
        return result

    @staticmethod
    def get_shared_files_context(user_id: int, limit: int = 5) -> str:
        from database import get_system_files

        files = get_system_files(user_id, scope="recent", limit=limit)
        if not files:
            return ""
        lines = ["Общие файлы пользователя:"]
        for f in files:
            lines.append(f"- #{f[0]} {f[2] or f[1]} ({f[4]})")
        return "\n".join(lines)

    @staticmethod
    async def chat(
        user_id: int,
        agent_code: str,
        message: str,
        context_depth: int = 10,
    ) -> str:
        from database import (
            get_ai_agent,
            get_ai_dialog_history_for_llm,
            add_ai_dialog_message,
            format_memory_context,
            get_ai_settings,
        )

        if not AIAgentService.can_access_agent(user_id, agent_code):
            return "Нет доступа к этому AI-агенту."

        agent = get_ai_agent(agent_code)
        if not agent:
            return "Агент не найден."

        _id, code, name, desc, model, prompt, active = agent
        settings = get_ai_settings(user_id)
        memory = format_memory_context(user_id)
        files_ctx = AIAgentService.get_shared_files_context(user_id)

        system_parts = [prompt or f"Ты {name}."]
        if files_ctx:
            system_parts.append(files_ctx)
        if memory:
            system_parts.append(memory)

        history = get_ai_dialog_history_for_llm(user_id, agent_code, context_depth)
        history.append({"role": "user", "content": message})
        add_ai_dialog_message(user_id, agent_code, "user", message)

        ai_settings = dict(settings)
        ai_settings["model"] = model or MODEL
        full_messages = history
        answer = await ask_openrouter(
            full_messages,
            user_memory="\n\n".join(system_parts),
            ai_settings=ai_settings,
        )
        add_ai_dialog_message(user_id, agent_code, "assistant", answer)
        return answer

import json
import re

import aiohttp

from config import OPENROUTER_API_KEY

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "openai/gpt-5-mini"

MEMORY_KEYS = ("name", "company", "city", "country", "activity", "interests")

BASE_SYSTEM_PROMPT = """
Ты персональный AI-помощник Фомы.

Правила:
- отвечай всегда на русском языке;
- отвечай кратко, если не просят подробно;
- хорошо разбирайся в строительстве;
- разбирайся в криптовалюте, USDT, международных платежах;
- разбирайся в законодательстве Украины;
- помогай писать документы, договоры и расчеты;
- если информации недостаточно — сначала задай уточняющие вопросы;
- используй известную информацию о пользователе в ответах, если она релевантна;
- не выдумывай факты о пользователе — опирайся только на переданную память.
"""


async def _call_openrouter(messages: list) -> str:
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": MODEL,
        "messages": messages,
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(OPENROUTER_URL, headers=headers, json=payload) as response:
            data = await response.json()

            if "choices" not in data:
                raise Exception(f"Ошибка OpenRouter: {data}")

            return data["choices"][0]["message"]["content"]


def _build_system_prompt(user_memory: str = "") -> str:
    prompt = BASE_SYSTEM_PROMPT.strip()
    if user_memory:
        prompt += f"\n\n{user_memory.strip()}"
    return prompt


def _parse_memory_json(raw: str) -> dict:
    text = raw.strip()
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        return {}

    try:
        data = json.loads(match.group())
    except json.JSONDecodeError:
        return {}

    if not isinstance(data, dict):
        return {}

    return {
        key: str(data[key]).strip()
        for key in MEMORY_KEYS
        if key in data and data[key]
    }


async def extract_memory_from_message(
    message: str,
    existing_profile: dict,
) -> dict:
    known = "\n".join(
        f"- {key}: {value}"
        for key, value in existing_profile.items()
    ) or "нет"

    extraction_prompt = f"""
Из сообщения пользователя извлеки только новую или обновлённую личную информацию.

Поля:
- name — имя
- company — компания
- city — город
- country — страна
- activity — сфера деятельности
- interests — интересы

Уже известно:
{known}

Сообщение пользователя:
{message}

Верни только JSON-объект с ключами name, company, city, country, activity, interests.
Если поле не упоминается или не меняется — верни пустую строку для этого ключа.
Пример: {{"name":"","company":"","city":"","country":"","activity":"","interests":""}}
"""

    raw = await _call_openrouter([
        {
            "role": "system",
            "content": "Ты извлекаешь структурированные данные. Отвечай только валидным JSON.",
        },
        {"role": "user", "content": extraction_prompt},
    ])

    return _parse_memory_json(raw)


async def ask_openrouter(messages: list, user_memory: str = "") -> str:
    system_prompt = _build_system_prompt(user_memory)
    full_messages = [{"role": "system", "content": system_prompt}] + messages
    return await _call_openrouter(full_messages)

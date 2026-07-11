import aiohttp

from config import OPENROUTER_API_KEY

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "openai/gpt-5-mini"


async def ask_openrouter(messages: list) -> str:
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": MODEL,
        "messages": [
    {
        "role": "system",
        "content": """
Ты персональный AI-помощник Фомы.

Правила:
- отвечай всегда на русском языке;
- отвечай кратко, если не просят подробно;
- хорошо разбирайся в строительстве;
- разбирайся в криптовалюте, USDT, международных платежах;
- разбирайся в законодательстве Украины;
- помогай писать документы, договоры и расчеты;
- если информации недостаточно — сначала задай уточняющие вопросы.
"""
    },
        *messages
],
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(OPENROUTER_URL, headers=headers, json=payload) as response:
            data = await response.json()
            return data["choices"][0]["message"]["content"]

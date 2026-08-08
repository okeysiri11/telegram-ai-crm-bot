# Voice Runtime — Command Center

Голосовые команды (RU) парсятся в `platform_ai_command/voice/parser.py`:

- Открой CRM
- Создай клиента
- Покажи прибыль
- Создай рекламу
- Сделай Reels
- Создай видео
- Озвучь ролик
- Опубликуй
- …

`parse_voice_transcript` → канонический текст → Command Router → Hercules.

Telegram: кнопка «🎙 Голосовой режим».
Web: кнопка 🎙 в AI Command Center.

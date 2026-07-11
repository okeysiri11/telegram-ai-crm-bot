# TelegramBotCourse

A basic Telegram bot project built with [aiogram](https://docs.aiogram.dev/).

## Project structure

```
TelegramBotCourse/
├── bot.py            # Bot entry point
├── config.py         # Configuration (loads settings from .env)
├── requirements.txt  # Python dependencies
├── .env              # Environment variables (bot token, etc.)
├── .gitignore
└── README.md
```

## Setup

1. Create and activate a virtual environment:

   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Set your bot token in the `.env` file:

   ```
   BOT_TOKEN=your_telegram_bot_token_here
   ```

4. Run the bot:

   ```bash
   python bot.py
   ```

## Requirements

- Python 3.10+
- [aiogram](https://pypi.org/project/aiogram/)
- [python-dotenv](https://pypi.org/project/python-dotenv/)
- [aiohttp](https://pypi.org/project/aiohttp/)

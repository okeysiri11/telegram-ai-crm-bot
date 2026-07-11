import os

from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

OWNER_ID = 1208044579
MANAGER_ID = 8312013093

MANAGERS = {
    8312013093: "Tony"
}
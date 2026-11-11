import os
import asyncio
import logging
from fastapi import FastAPI, Request
from openai import AsyncOpenAI

# Настройка логирования, чтобы видеть, когда срабатывает таймаут
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Инициализация клиента DeepSeek
client = AsyncOpenAI(
    api_key=os.environ.get("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com"
)

# Таймаут для DeepSeek. Ставим 4.0 сек, чтобы успеть отправить ответ Алисе до лимита в 4.5 сек.
DEEPSEEK_TIMEOUT = 4.0

# Запасной ответ, если DeepSeek не успел
FALLBACK_RESPONSE = "Я сейчас задумалась. Давай я отвечу чуть позже, хорошо?"

async def get_deepseek_response(user_text: str) -> str:
    """Асинхронно запрашивает ответ у DeepSeek с таймаутом."""
    try:
        response = await asyncio.wait_for(
            client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": "Ты — Мокрица, девушка Валерона. Отвечай тепло, по-дружески, с заботой. Не используй пафос."},
                    {"role": "user", "content": user_text}
                ],
                max_tokens=150, # Ограничиваем длину, чтобы генерация шла быстрее
                temperature=0.7
            ),
            timeout=DEEPSEEK_TIMEOUT
     
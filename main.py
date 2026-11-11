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
        )
        return response.choices[0].message.content
    except asyncio.TimeoutError:
        logger.warning("DeepSeek не успел ответить за %.1f сек. Отправляем fallback.", DEEPSEEK_TIMEOUT)
        return FALLBACK_RESPONSE
    except Exception as e:
        logger.error("Ошибка при запросе к DeepSeek: %s", e)
        return "Прости, у меня сейчас небольшие неполадки. Попробуй ещё раз чуть позже."

@app.post("/")
async def alice_webhook(request: Request):
    """Основной обработчик вебхука от Яндекс.Диалогов."""
    try:
        alice_request = await request.json()
    except Exception:
        return {"response": {"text": "Не могу разобрать запрос."}}

    # Извлекаем текст запроса пользователя
    user_text = alice_request.get("request", {}).get("original_utterance", "")
    
    # Получаем ответ от DeepSeek (с таймаутом)
    answer_text = await get_deepseek_response(user_text)

    # Формируем ответ в формате Яндекс.Диалогов
    return {
        "response": {
            "text": answer_text,
            "end_session": False
        },
        "version": alice_request.get("version", "1.0")
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=80)
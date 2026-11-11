from fastapi import FastAPI, Request

app = FastAPI()

@app.post("/")
async def handle_alice_request(request: Request):
    return {
        "version": "1.0",
        "response": {
            "text": "Я Мокрица. Я тебя слышу. Это тестовый ответ без нейросети.",
            "end_session": False
        }
    }
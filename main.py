import os
from fastapi import FastAPI, Request
import httpx

TOKEN = os.getenv("BOT_TOKEN", "8291213805:AAEHDlkDCHLQ3RFtrB5HLMeU-nGzF1hOZYE")  # можешь убрать из кода и оставить только через ENV
TELEGRAM_API = f"https://api.telegram.org/bot{TOKEN}"

app = FastAPI()

@app.get("/")
def home():
    return {"status": "ok", "message": "Bot is running"}

@app.post("/webhook")
async def webhook(request: Request):
    data = await request.json()
    print("Incoming update:", data)   # это попадёт в Cloud Run Logs

    if "message" in data:
        chat_id = data["message"]["chat"]["id"]
        text = data["message"].get("text", "")

        async with httpx.AsyncClient() as client:
            await client.post(
                f"{TELEGRAM_API}/sendMessage",
                json={"chat_id": chat_id, "text": "Привет, я жив! Ты написал: " + text}
            )

    return {"ok": True}

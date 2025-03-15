import os
import requests
import threading
import asyncio
from dotenv import load_dotenv
from flask import Flask
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
from transformers import pipeline

# ✅ Load environment variables
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
HF_API_KEY = os.getenv("HF_API_KEY")

# ✅ Check if bot token is missing
if not TOKEN:
    raise ValueError("⚠️ BOT_TOKEN is missing! Check .env file.")

# ✅ Initialize Flask server (Prevents Google Cloud from shutting down)
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

# ✅ AI Function: First Try Hugging Face API, Then Together AI, Then Local Model
def chatbot_response(user_input):
    """ Handles AI responses using Hugging Face API, Together AI, or local model. """

    # ✅ Option 1: Use Hugging Face API (if key is set)
    if HF_API_KEY:
        headers = {"Authorization": f"Bearer {HF_API_KEY}"}
        data = {"inputs": user_input}

        response = requests.post(
            "https://api-inference.huggingface.co/models/facebook/blenderbot-400M-distill",
            json=data, headers=headers
        )

        if response.status_code == 200:
            return response.json().get("generated_text", "I couldn't process that.")
        elif response.status_code == 403:
            return "❌ API Error 403: Hugging Face model access restricted."
        else:
            print(f"⚠️ Hugging Face API Error: {response.status_code} - {response.text}")

    # ✅ Option 2: Use Together AI (if Hugging Face fails)
    url = "https://api.together.xyz/inference"
    data = {
        "model": "openchat/openchat-3.5-0106",
        "prompt": user_input,
        "max_tokens": 250
    }
    headers = {"Content-Type": "application/json"}

    response = requests.post(url, json=data, headers=headers)
    if response.status_code == 200:
        return response.json().get("text", "I couldn't process that.")
    elif response.status_code == 401:
        return "⚠️ API access restricted. Trying another model..."
    else:
        print(f"⚠️ Together AI Error: {response.status_code} - {response.text}")

    # ✅ Option 3: Use Local Model as Fallback
    print("⚠️ Falling back to local AI model...")
    local_chatbot = pipeline("text-generation", model="microsoft/DialoGPT-medium")
    response = local_chatbot(user_input, max_length=100, pad_token_id=50256)
    return response[0]['generated_text']

# ✅ Start the bot manually
async def startbot(update: Update, context: CallbackContext):
    await update.message.reply_text("✅ The bot is now active! You can chat and use commands.")

# ✅ Stop the bot manually
async def stopbot(update: Update, context: CallbackContext):
    await update.message.reply_text("❌ The bot has been deactivated. Type `/startbot` when you need it again.")

# ✅ Handle messages (route them to AI)
async def chat(update: Update, context: CallbackContext):
    user_text = update.message.text.strip()
    response = chatbot_response(user_text)
    await update.message.reply_text(response)

# ✅ Initialize Telegram Bot
bot_app = Application.builder().token(TOKEN).build()
bot_app.add_handler(CommandHandler("startbot", startbot))
bot_app.add_handler(CommandHandler("stopbot", stopbot))
bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))

# ✅ Run Flask & Telegram Bot
def run_flask():
    app.run(host="0.0.0.0", port=5000)

flask_thread = threading.Thread(target=run_flask)
flask_thread.start()

asyncio.run(bot_app.run_polling())

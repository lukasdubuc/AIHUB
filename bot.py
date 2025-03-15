from dotenv import load_dotenv
import os
import nest_asyncio
import requests
import threading
import asyncio
from flask import Flask
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
from transformers import pipeline

# ✅ Load environment variables
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
HF_API_KEY = os.getenv("HF_API_KEY")  # ✅ Using one key for both Hugging Face & Together AI

# ✅ Ensure BOT_TOKEN exists
if not TOKEN:
    raise ValueError("⚠️ BOT_TOKEN is missing! Check environment variables.")

# ✅ Initialize Flask app
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

# ✅ Track bot status
bot_active = False  # Default OFF

# ✅ AI Response Function
def chatbot_response(user_input):
    """Handles AI responses via Hugging Face API, Together AI, or local model."""
    print(f"🔹 User Input: {user_input}")  # Debugging input

    # ✅ Try Hugging Face API first
    if HF_API_KEY:
        headers = {"Authorization": f"Bearer {HF_API_KEY}"}
        data = {"inputs": user_input}
        response = requests.post(
            "https://api-inference.huggingface.co/models/facebook/blenderbot-400M-distill",
            json=data, headers=headers
        )
        print(f"🔹 Hugging Face API Response: {response.status_code} - {response.text}")

        if response.status_code == 200:
            result = response.json()
            print(f"🔍 Hugging Face Response JSON: {result}")  # Log full API response

            if isinstance(result, list) and len(result) > 0 and isinstance(result[0], dict):
                return result[0].get("generated_text", "⚠️ Unexpected response format.")
            elif isinstance(result, dict) and "generated_text" in result:
                return result["generated_text"]
            return f"⚠️ Unexpected response format from Hugging Face: {result}"
        print(f"⚠️ Hugging Face API Error: {response.status_code} - {response.text}")

    # ✅ Fallback to Together AI (Using the same HF_API_KEY)
    together_url = "https://api.together.xyz/inference"
    headers = {
        "Authorization": f"Bearer {HF_API_KEY}",  # ✅ Uses the same Hugging Face API key
        "Content-Type": "application/json"
    }
    data = {"model": "mistralai/Mixtral-8x7B-Instruct-v0.1", "prompt": user_input, "max_tokens": 300}

    try:
        response = requests.post(together_url, json=data, headers=headers)
        print(f"🔹 Together AI API Response: {response.status_code} - {response.text}")

        if response.status_code == 200:
            result = response.json()
            print(f"🔍 Together AI Response JSON: {result}")  # Log full API response

            if isinstance(result, dict) and "text" in result:
                return result["text"]
            return f"⚠️ Unexpected response format from Together AI: {result}"
        print(f"⚠️ Together AI Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"⚠️ Together AI Request Error: {str(e)}")

    # ✅ Final fallback: Local AI Model
    print("⚠️ Falling back to local AI model...")
    local_chatbot = pipeline("text-generation", model="microsoft/DialoGPT-medium")
    response = local_chatbot(user_input, max_length=100, pad_token_id=50256)
    return response[0]['generated_text']

# ✅ Start the bot manually
async def startbot(update: Update, context: CallbackContext):
    global bot_active
    bot_active = True
    await update.message.reply_text("✅ Bot is now active! You can chat and use commands.")

# ✅ Stop the bot manually
async def stopbot(update: Update, context: CallbackContext):
    global bot_active
    bot_active = False
    await update.message.reply_text("❌ Bot has been deactivated. Use /startbot to activate again.")

# ✅ Handle user messages
async def chat(update: Update, context: CallbackContext):
    user_text = update.message.text.strip()
    response = chatbot_response(user_text)
    await update.message.reply_text(response)

# ✅ Initialize Telegram Bot
bot_app = Application.builder().token(TOKEN).build()
bot_app.add_handler(CommandHandler("startbot", startbot))
bot_app.add_handler(CommandHandler("stopbot", stopbot))
bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))

print("✅ Bot is ready!")
print("🌍 Running on macOS/Linux-compatible setup")

# ✅ Run Flask & Telegram Bot Together
def run_flask():
    """Run Flask app on a separate thread."""
    from waitress import serve  # macOS-compatible production server
    serve(app, host="0.0.0.0", port=5000)

# Start Flask in a separate thread
flask_thread = threading.Thread(target=run_flask, daemon=True)
flask_thread.start()

# ✅ Start Telegram bot polling (Fixes macOS asyncio issue)
nest_asyncio.apply()
asyncio.run(bot_app.run_polling())
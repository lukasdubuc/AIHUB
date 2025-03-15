<<<<<<< HEAD
from dotenv import load_dotenv
=======
<<<<<<< HEAD
=======
from dotenv import load_dotenv
import os

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise ValueError("Error: BOT_TOKEN is missing! Check .env file.")

import nest_asyncio
>>>>>>> 41b77cc (Updated bot.py, added requirements.txt and .env, removed requirements.text)
>>>>>>> 52ee38b (Updated bot.py, added requirements.txt and .env, removed requirements.text)
import os
import requests
import threading
import asyncio
import nest_asyncio
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

<<<<<<< HEAD
# ✅ Track bot status
bot_active = False  # Bot is OFF by default

# ✅ AI Function: Try Hugging Face API, Then Together AI (Mixtral), Then Local Model
=======
<<<<<<< HEAD
# ✅ AI Function: First Try Hugging Face API, Then Together AI, Then Local Model
>>>>>>> 52ee38b (Updated bot.py, added requirements.txt and .env, removed requirements.text)
def chatbot_response(user_input):
    """Handles AI responses using Hugging Face API, Together AI, or local model."""
    if not bot_active:
        return "❌ Bot is inactive. Use /startbot to activate it."

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

    # ✅ Option 2: Use Together AI with Mixtral model
    url = "https://api.together.xyz/inference"
    data = {
        "model": "mistralai/Mixtral-8x7B-Instruct-v0.1",  # Updated to Mixtral from 41b77cc
        "prompt": user_input,
        "max_tokens": 300  # Increased from 250 per 41b77cc
    }
    headers = {"Content-Type": "application/json"}
    try:
        response = requests.post(url, json=data, headers=headers)
        if response.status_code == 200:
            return response.json().get("text", "I couldn't process that.")
        elif response.status_code == 401:
            return "⚠️ API access restricted. Trying another model..."
        else:
            return f"❌ API Error {response.status_code}: {response.text}"
    except Exception as e:
        print(f"⚠️ Together AI Error: {str(e)}")

    # ✅ Option 3: Use Local Model as Fallback
    print("⚠️ Falling back to local AI model...")
    local_chatbot = pipeline("text-generation", model="microsoft/DialoGPT-medium")
    response = local_chatbot(user_input, max_length=100, pad_token_id=50256)
    return response[0]['generated_text']
=======
# ✅ Get Bot Token from Railway Variables
TOKEN = os.getenv("BOT_TOKEN")

# ✅ Track bot status
bot_active = False  # ✅ New: Bot is OFF by default

# ✅ Chatbot response
import requests

def chatbot_response(user_input):
    url = "https://api.together.xyz/inference"
    data = {
        "model": "mistralai/Mixtral-8x7B-Instruct-v0.1",  # Switch to Mixtral AI
        "prompt": user_input,
        "max_tokens": 300  # Increase for longer responses
    }
    headers = {"Content-Type": "application/json"}

    try:
        response = requests.post(url, json=data, headers=headers)
        if response.status_code == 200:
            return response.json().get("text", "I couldn't process that.")
        elif response.status_code == 401:
            return "⚠️ API access restricted. Trying another model..."
        else:
            return f"❌ API Error {response.status_code}: {response.text}"
    except Exception as e:
        return f"❌ Request failed: {str(e)}"

>>>>>>> 41b77cc (Updated bot.py, added requirements.txt and .env, removed requirements.text)

# ✅ Start the bot manually
async def startbot(update: Update, context: CallbackContext):
    global bot_active
    bot_active = True
    await update.message.reply_text("✅ The bot is now active! You can chat and use commands.")

# ✅ Stop the bot manually
async def stopbot(update: Update, context: CallbackContext):
    global bot_active
    bot_active = False
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

print("This is my local version of bot.py")
print("This is the GitHub version of bot.py")


# ✅ Run Flask & Telegram Bot
<<<<<<< HEAD
=======
import threading
import asyncio

>>>>>>> 41b77cc (Updated bot.py, added requirements.txt and .env, removed requirements.text)
def run_flask():
    app.run(host="0.0.0.0", port=5000)

# Start Flask in a separate thread
flask_thread = threading.Thread(target=run_flask)
flask_thread.start()

<<<<<<< HEAD
# Start Telegram bot polling
nest_asyncio.apply()  # Added to handle nested asyncio in some environments
=======
<<<<<<< HEAD
>>>>>>> 52ee38b (Updated bot.py, added requirements.txt and .env, removed requirements.text)
asyncio.run(bot_app.run_polling())
=======
# Start Telegram bot polling
asyncio.run(bot_app.run_polling())

>>>>>>> 41b77cc (Updated bot.py, added requirements.txt and .env, removed requirements.text)

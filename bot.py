import json
import os
import asyncio
import nest_asyncio
from flask import Flask
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext

# ✅ Prevent async issues
nest_asyncio.apply()

# ✅ Set up Flask server (Keeps Google Cloud from shutting down)
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

# ✅ Load API Tokens from `api_config.json`
try:
    with open("api_config.json", "r") as file:
        config = json.load(file)
    BOT_TOKEN = config["BOT_TOKEN"]
    HK_API_KEY = config["HK_API_KEY"]  # Correct HK API Key Handling
except Exception as e:
    print("❌ Error loading API config:", e)
    exit(1)

# ✅ Track bot status
bot_active = False  # ✅ Bot starts OFF

# ✅ Chatbot responses
def chatbot_response(user_input):
    responses = {
        "hi": "Hello! How can I assist you today?",
        "hello": "Hey there! What’s on your mind?",
        "how are you": "I'm just an AI, but I'm doing great! How about you?",
        "what can you do": "I can chat, help with business automation, and assist with product creation.",
        "who are you": "I'm your AI assistant, here to help you manage and grow your business!"
    }
    return responses.get(user_input.lower(), "I'm here to chat! Let me know how I can help.")

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
    print("Bot has been manually stopped.")

# ✅ Handle messages (only if bot is active)
async def chat(update: Update, context: CallbackContext):
    global bot_active
    if not bot_active:
        return  # ✅ Ignore messages when the bot is off

    user_text = update.message.text.strip()
    response = chatbot_response(user_text)
    await update.message.reply_text(response)

# ✅ Show API Keys (For Debugging, Safe Truncated Display)
async def show_apikeys(update: Update, context: CallbackContext):
    global bot_active
    if not bot_active:
        return

    await update.message.reply_text(f"🔑 HK API Key: {HK_API_KEY[:10]}...")

# ✅ Initialize Telegram Bot
bot_app = Application.builder().token(BOT_TOKEN).build()

# ✅ Add Handlers
bot_app.add_handler(CommandHandler("startbot", startbot))  # ✅ Start bot manually
bot_app.add_handler(CommandHandler("stopbot", stopbot))    # ✅ Stop bot manually
bot_app.add_handler(CommandHandler("showapikeys", show_apikeys))  # ✅ Show HK API Key
bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))

print("Bot is ready but inactive until started.")

# ✅ Run Flask & Telegram Bot
import threading

def run_flask():
    app.run(host="0.0.0.0", port=5000)

flask_thread = threading.Thread(target=run_flask)
flask_thread.start()

asyncio.get_event_loop().run_until_complete(bot_app.run_polling())
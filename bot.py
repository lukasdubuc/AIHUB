import nest_asyncio
import os
import asyncio
from flask import Flask
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext

# ✅ Prevent async issues
nest_asyncio.apply()

# ✅ Set up Flask server (Keeps Railway from shutting down)
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is ready, but inactive until you start it."

# ✅ Get Bot Token from Railway Variables
TOKEN = os.getenv("BOT_TOKEN")

# ✅ Track bot status
bot_active = False  # ✅ New: Bot is OFF by default

# ✅ Chatbot responses
import requests
import os
from dotenv import load_dotenv

load_dotenv()
HF_API_KEY = os.getenv("HF_API_KEY")

def chatbot_response(user_input):
    headers = {"Authorization": f"Bearer {HF_API_KEY}"}
    data = {"inputs": user_input}
    
    response = requests.post(
        "https://api-inference.huggingface.co/models/mistralai/Mixtral-8x7B-Instruct-v0.1",
        json=data, headers=headers
    )

    if response.status_code == 200:
        return response.json().get("generated_text", "I couldn't process that.")
    else:
        return f"❌ API Error {response.status_code}: {response.text}"


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

# ✅ Advanced Features (No Password Required)
async def advanced_services(update: Update, context: CallbackContext):
    global bot_active
    if not bot_active:
        return  # ✅ Ignore if the bot is off

    await update.message.reply_text("🚀 Advanced services are available! What would you like to do today?")

# ✅ Initialize Telegram Bot
bot_app = Application.builder().token(TOKEN).build()

# ✅ Add Handlers
bot_app.add_handler(CommandHandler("startbot", startbot))  # ✅ Start bot manually
bot_app.add_handler(CommandHandler("stopbot", stopbot))    # ✅ Stop bot manually
bot_app.add_handler(CommandHandler("services", advanced_services))
bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))

print("Bot is ready, but inactive until started.")

# ✅ Run Flask & Telegram Bot
import threading

def run_flask():
    app.run(host="0.0.0.0", port=5000)

flask_thread = threading.Thread(target=run_flask)
flask_thread.start()

asyncio.get_event_loop().run_until_complete(bot_app.run_polling())

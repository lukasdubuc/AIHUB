import json
import asyncio
import nest_asyncio
import requests
from flask import Flask
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
import threading

# Prevent async issues
nest_asyncio.apply()

# Set up Flask server (Keeps Google Cloud alive)
app = Flask(__name__)

@app.route('/')
def home():
    return "AI Chatbot is running!"

# Load API Tokens from `api_config.json`
CONFIG_PATH = "/home/lukasdubuc/AIHUB/api_config.json"

try:
    with open(CONFIG_PATH, "r") as file:
        config = json.load(file)
    BOT_TOKEN = config.get("BOT_TOKEN", "")
    HF_API_KEY = config.get("HF_API_KEY", "")
except Exception as e:
    print(f"❌ Error loading API config: {e}")
    exit(1)

# Track bot status
bot_active = False

# Chatbot Response (Using Hugging Face API)
def chatbot_response(user_input):
    """Handles AI responses via Hugging Face API."""
    if not bot_active:
        return "❌ Bot is inactive. Use /startbot to activate."

    if not HF_API_KEY:
        return "❌ No Hugging Face API key provided."

    try:
        headers = {"Authorization": f"Bearer {HF_API_KEY}", "Content-Type": "application/json"}
        data = {"inputs": user_input}
        response = requests.post(
            "https://api-inference.huggingface.co/models/facebook/blenderbot-400M-distill",
            headers=headers,
            json=data
        )
        response_data = response.json()

        # Handle list response (e.g., [{'generated_text': 'some text'}])
        if isinstance(response_data, list) and len(response_data) > 0:
            if isinstance(response_data[0], dict) and "generated_text" in response_data[0]:
                return response_data[0]["generated_text"]
            return "Unexpected response format from Hugging Face API."
        # Handle dict response (e.g., {'generated_text': 'some text'})
        elif isinstance(response_data, dict) and "generated_text" in response_data:
            return response_data["generated_text"]
        else:
            return "Unexpected response structure from Hugging Face API."
    except requests.exceptions.RequestException as e:
        print(f"❌ Network error: {e}")
        return "I'm having trouble connecting to the Hugging Face API."
    except Exception as e:
        print(f"❌ Error in chatbot_response: {e}")
        return "Sorry, an unexpected error occurred."

# Telegram Command Handlers
async def startbot(update: Update, context: CallbackContext):
    global bot_active
    bot_active = True
    await update.message.reply_text("✅ The AI Chatbot is now active! Start chatting with me.")

async def stopbot(update: Update, context: CallbackContext):
    global bot_active
    bot_active = False
    await update.message.reply_text("❌ The AI Chatbot is deactivated. Use `/startbot` to reactivate.")
    print("AI Chatbot has been manually stopped.")

async def chat(update: Update, context: CallbackContext):
    global bot_active
    if not bot_active:
        return

    user_text = update.message.text.strip()
    response = chatbot_response(user_text)
    await update.message.reply_text(response)

# Error Handler for Telegram
async def error_handler(update: Update, context: CallbackContext):
    print(f"❌ Exception occurred: {context.error}")
    try:
        await update.message.reply_text("Sorry, something went wrong. Please try again.")
    except Exception:
        pass  # Avoid infinite loop if reply fails

# Initialize Telegram Bot
bot_app = Application.builder().token(BOT_TOKEN).build()

# Add Handlers
bot_app.add_handler(CommandHandler("startbot", startbot))
bot_app.add_handler(CommandHandler("stopbot", stopbot))
bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))
bot_app.add_error_handler(error_handler)

print("✅ AI Chatbot is ready but inactive until started.")

# Run Flask & Telegram Bot
def run_flask():
    app.run(host="0.0.0.0", port=5000)

flask_thread = threading.Thread(target=run_flask)
flask_thread.start()

asyncio.get_event_loop().run_until_complete(bot_app.run_polling())

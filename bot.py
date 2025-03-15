import json
import os
import asyncio
import nest_asyncio
import requests
from flask import Flask
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext

# Prevent async issues
nest_asyncio.apply()

# Set up Flask server (Keeps Google Cloud alive)
app = Flask(__name__)

@app.route('/')
def home():
    return "AI Hub Bot is running!"

# Load API Tokens from `api_config.json`
CONFIG_PATH = "/home/lukasdubuc/AIHUB/api_config.json"

try:
    with open(CONFIG_PATH, "r") as file:
        config = json.load(file)
    BOT_TOKEN = config.get("BOT_TOKEN", "")
    HK_API_KEY = config.get("HK_API_KEY", "")
    AI_API_URL = "https://your-hk-ai-api-endpoint.com/generate"  # Replace with your AI API URL
except Exception as e:
    print(f"❌ Error loading API config: {e}")
    exit(1)

# Track bot status
bot_active = False

# AI Supervisor Function (Delegates to Specialized Agents)
def ai_supervisor(user_input):
    """Delegates tasks to specialized AI agents or returns a chatbot response."""
    user_input_lower = user_input.lower()

    if "write" in user_input_lower:
        os.system("python3 /home/lukasdubuc/AIHUB/ai_writer.py")
        return "📝 AI Writer is generating content! Check the terminal for input."
    elif "generate image" in user_input_lower:
        os.system("python3 /home/lukasdubuc/AIHUB/ai_image.py")
        return "🎨 AI Image Generator is creating an image! Check the terminal for input."
    elif "generate video" in user_input_lower:
        os.system("python3 /home/lukasdubuc/AIHUB/ai_video.py")
        return "🎬 AI Video Generator is processing a video! Check the terminal for input."
    elif "sync shopify" in user_input_lower:
        os.system("python3 /home/lukasdubuc/AIHUB/ai_shopify.py")
        return "🛒 E-commerce AI is syncing your Shopify store!"
    elif "schedule" in user_input_lower or "automate" in user_input_lower:
        os.system("python3 /home/lukasdubuc/AIHUB/ai_scheduler.py")
        return "⏰ AI Scheduler is setting up your task! Check the terminal for input."
    else:
        return chatbot_response(user_input)

# Chatbot Response Function (Fallback for General Queries)
def chatbot_response(user_input):
    try:
        headers = {
            "Authorization": f"Bearer {HK_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {"input": user_input}

        response = requests.post(AI_API_URL, json=payload, headers=headers)
        response_data = response.json()

        if isinstance(response_data, list) and len(response_data) > 0:
            if isinstance(response_data[0], dict) and "generated_text" in response_data[0]:
                return response_data[0]["generated_text"]
            else:
                return "Unexpected response format from AI API."
        elif isinstance(response_data, dict) and "generated_text" in response_data:
            return response_data["generated_text"]
        else:
            return "Unexpected response structure from AI API."

    except requests.exceptions.RequestException as e:
        print(f"❌ Network error: {e}")
        return "I'm having trouble connecting to the AI service."
    except Exception as e:
        print(f"❌ Error in chatbot_response: {e}")
        return "Sorry, an unexpected error occurred."

# Telegram Command Handlers
async def startbot(update: Update, context: CallbackContext):
    global bot_active
    bot_active = True
    await update.message.reply_text("✅ The AI Hub is now active! Chat or use commands to delegate tasks.")

async def stopbot(update: Update, context: CallbackContext):
    global bot_active
    bot_active = False
    await update.message.reply_text("❌ The AI Hub is deactivated. Use `/startbot` to reactivate.")
    print("AI Hub has been manually stopped.")

async def chat(update: Update, context: CallbackContext):
    global bot_active
    if not bot_active:
        return

    user_text = update.message.text.strip()
    response = ai_supervisor(user_text)
    await update.message.reply_text(response)

async def show_apikey(update: Update, context: CallbackContext):
    global bot_active
    if not bot_active:
        return
    await update.message.reply_text(f"🔑 HK API Key: {HK_API_KEY[:10]}...")

# Initialize Telegram Bot
bot_app = Application.builder().token(BOT_TOKEN).build()

# Add Handlers
bot_app.add_handler(CommandHandler("startbot", startbot))
bot_app.add_handler(CommandHandler("stopbot", stopbot))
bot_app.add_handler(CommandHandler("showapikey", show_apikey))
bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))

print("✅ AI Hub Bot is ready but inactive until started.")

# Run Flask & Telegram Bot
import threading

def run_flask():
    app.run(host="0.0.0.0", port=5000)

flask_thread = threading.Thread(target=run_flask)
flask_thread.start()

asyncio.get_event_loop().run_until_complete(bot_app.run_polling())

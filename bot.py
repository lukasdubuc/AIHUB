import json
import asyncio
import nest_asyncio
import requests
from flask import Flask
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
from transformers import pipeline
from diffusers import StableDiffusionPipeline
import torch
import schedule
import time
import threading
import io

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

# Initialize AI Models (Load once for efficiency)
text_generator = pipeline("text-generation", model="gpt2")
try:
    image_generator = StableDiffusionPipeline.from_pretrained("runwayml/stable-diffusion-v1-5")
    image_generator.to("cuda" if torch.cuda.is_available() else "cpu")
except Exception as e:
    print(f"❌ Error loading image generator: {e}")
    image_generator = None

# AI Supervisor Function (Delegates to Specialized Agents)
def ai_supervisor(user_input):
    """Delegates tasks to specialized AI agents or returns a chatbot response."""
    user_input_lower = user_input.lower()

    if "write" in user_input_lower:
        topic = user_input.replace("write", "").strip() or "default topic"
        return ai_writer(topic)
    elif "generate image" in user_input_lower:
        prompt = user_input.replace("generate image", "").strip() or "default image"
        return ai_image_generator(prompt)
    elif "generate video" in user_input_lower:
        prompt = user_input.replace("generate video", "").strip() or "default video"
        return ai_video_generator(prompt)
    elif "sync shopify" in user_input_lower:
        return ai_shopify()
    elif "schedule" in user_input_lower or "automate" in user_input_lower:
        return "⏰ Use '/schedule <task> <frequency> <time>' (e.g., '/schedule sync shopify daily 09:00')"
    else:
        return chatbot_response(user_input)

# Specialized AI Agents
def ai_writer(topic):
    try:
        response = text_generator(topic, max_length=200, num_return_sequences=1)
        return f"📝 Generated Content:\n{response[0]['generated_text']}"
    except Exception as e:
        return f"❌ Error in AI Writer: {e}"

def ai_image_generator(prompt):
    if not image_generator:
        return "❌ Image generator not available."
    try:
        image = image_generator(prompt).images[0]
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format="PNG")
        img_byte_arr.seek(0)
        return {"type": "image", "data": img_byte_arr}
    except Exception as e:
        return f"❌ Error in Image Generator: {e}"

def ai_video_generator(prompt):
    # Placeholder: Replace with your video generation logic or API
    return f"🎬 Video generation not fully implemented yet. Prompt: {prompt}"

def ai_shopify():
    # Placeholder: Replace with your Shopify API logic
    try:
        shopify_url = f"https://{API_KEY}:{PASSWORD}@your-store.myshopify.com/admin/api/2023-01/products.json"
        response = requests.get(shopify_url)
        if response.status_code == 200:
            data = response.json()
            return f"✅ Synced {len(data['products'])} products!"
        return "❌ Failed to sync Shopify store."
    except Exception as e:
        return f"❌ Error in Shopify Sync: {e}"

# Chatbot Response (Fallback for General Queries)
def chatbot_response(user_input):
    try:
        headers = {"Authorization": f"Bearer {HK_API_KEY}", "Content-Type": "application/json"}
        payload = {"input": user_input}
        response = requests.post(AI_API_URL, json=payload, headers=headers)
        response_data = response.json()

        if isinstance(response_data, list) and len(response_data) > 0:
            if isinstance(response_data[0], dict) and "generated_text" in response_data[0]:
                return response_data[0]["generated_text"]
            return "Unexpected response format from AI API."
        elif isinstance(response_data, dict) and "generated_text" in response_data:
            return response_data["generated_text"]
        return "Unexpected response structure from AI API."
    except Exception as e:
        return f"❌ Error in chatbot_response: {e}"

# Scheduler Logic
scheduled_tasks = []

def run_scheduled_tasks():
    while True:
        schedule.run_pending()
        time.sleep(60)

def schedule_task(task, frequency, time_str):
    def run_task():
        result = ai_supervisor(task)
        print(f"✅ Scheduled task '{task}' executed: {result}")

    if frequency.lower() == "daily":
        schedule.every().day.at(time_str).do(run_task)
    elif frequency.lower() == "weekly":
        schedule.every().monday.at(time_str).do(run_task)
    else:
        return "❌ Frequency must be 'daily' or 'weekly'."
    scheduled_tasks.append({"task": task, "frequency": frequency, "time": time_str})
    return f"✅ Scheduled '{task}' to run {frequency} at {time_str}!"

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
    
    if isinstance(response, dict) and response["type"] == "image":
        await update.message.reply_photo(photo=response["data"])
    else:
        await update.message.reply_text(response)

async def schedule_command(update: Update, context: CallbackContext):
    global bot_active
    if not bot_active:
        return
    
    try:
        args = context.args
        if len(args) < 3:
            await update.message.reply_text("❌ Usage: /schedule <task> <frequency> <time> (e.g., '/schedule sync shopify daily 09:00')")
            return
        task = " ".join(args[:-2])
        frequency, time_str = args[-2], args[-1]
        response = schedule_task(task, frequency, time_str)
        await update.message.reply_text(response)
    except Exception as e:
        await update.message.reply_text(f"❌ Error scheduling: {e}")

# Commented out for security (uncomment for debugging)
# async def show_apikey(update: Update, context: CallbackContext):
#     global bot_active
#     if not bot_active:
#         return
#     await update.message.reply_text(f"🔑 HK API Key: {HK_API_KEY[:10]}...")

# Initialize Telegram Bot
bot_app = Application.builder().token(BOT_TOKEN).build()

# Add Handlers
bot_app.add_handler(CommandHandler("startbot", startbot))
bot_app.add_handler(CommandHandler("stopbot", stopbot))
bot_app.add_handler(CommandHandler("schedule", schedule_command))
# bot_app.add_handler(CommandHandler("showapikey", show_apikey))  # Commented out for security
bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))

print("✅ AI Hub Bot is ready but inactive until started.")

# Run Flask & Telegram Bot
def run_flask():
    app.run(host="0.0.0.0", port=5000)

flask_thread = threading.Thread(target=run_flask)
flask_thread.start()

# Start scheduler in a separate thread
scheduler_thread = threading.Thread(target=run_scheduled_tasks)
scheduler_thread.start()

asyncio.get_event_loop().run_until_complete(bot_app.run_polling())

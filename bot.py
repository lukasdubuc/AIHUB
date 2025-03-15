import json
import asyncio
import nest_asyncio
import requests
from flask import Flask, request, jsonify
import threading

# Prevent async issues
nest_asyncio.apply()

# Set up Flask server (Keeps Replit instance alive)
app = Flask(__name__)

@app.route('/')
def home():
    return "✅ AI Hub is running!"

# Load API Tokens from `api_config.json`
CONFIG_PATH = "api_config.json"  # Change this path if needed

try:
    with open(CONFIG_PATH, "r") as file:
        config = json.load(file)
    HF_API_KEY = config.get("HF_API_KEY", "")
except Exception as e:
    print(f"❌ Error loading API config: {e}")
    exit(1)

# Chatbot Response (Using Hugging Face API)
def chatbot_response(user_input):
    """Handles AI responses via Hugging Face API."""
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

        if isinstance(response_data, list) and "generated_text" in response_data[0]:
            return response_data[0]["generated_text"]
        elif isinstance(response_data, dict) and "generated_text" in response_data:
            return response_data["generated_text"]
        else:
            return "Unexpected response from Hugging Face API."
    except requests.exceptions.RequestException as e:
        print(f"❌ Network error: {e}")
        return "I'm having trouble connecting to the Hugging Face API."
    except Exception as e:
        print(f"❌ Error in chatbot_response: {e}")
        return "An unexpected error occurred."

# AI Business Report (Using Hugging Face API)
def generate_business_report():
    """Generates an AI-driven business report."""
    return chatbot_response("Generate a weekly financial report with revenue, expenses, and insights.")

# Flask API - Get AI-Generated Business Report
@app.route('/business-report', methods=['GET'])
def business_report():
    report = generate_business_report()
    return jsonify({"report": report})

# Flask API - AI Chat Assistant
@app.route('/ask-ai', methods=['POST'])
def ask_ai():
    data = request.get_json()
    user_message = data.get("message", "")

    if not user_message:
        return jsonify({"error": "Message is required."}), 400

    response = chatbot_response(user_message)
    return jsonify({"response": response})

# Run Flask Server in a Thread (To Keep It Running on Replit)
def run_flask():
    app.run(host="0.0.0.0", port=5000)

flask_thread = threading.Thread(target=run_flask)
flask_thread.start()

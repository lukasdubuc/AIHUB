import express from "express";
import axios from "axios";
import dotenv from "dotenv";
import fs from "fs";

// Load environment variables
dotenv.config();

const app = express();
app.use(express.json());

// Load API key from config file
const CONFIG_PATH = "api_config.json";
let HF_API_KEY = "";

try {
  const config = JSON.parse(fs.readFileSync(CONFIG_PATH, "utf-8"));
  HF_API_KEY = config.HF_API_KEY || "";
} catch (error) {
  console.error("❌ Error loading API config:", error.message);
  process.exit(1);
}

// Home Route
app.get("/", (req, res) => {
  res.send("✅ AI Hub is running!");
});

// AI Chatbot Response
const chatbotResponse = async (userInput) => {
  if (!HF_API_KEY) {
    return "❌ No Hugging Face API key provided.";
  }

  try {
    const response = await axios.post(
      "https://api-inference.huggingface.co/models/facebook/blenderbot-400M-distill",
      { inputs: userInput },
      {
        headers: {
          Authorization: `Bearer ${HF_API_KEY}`,
          "Content-Type": "application/json",
        },
      }
    );

    if (response.data && response.data.generated_text) {
      return response.data.generated_text;
    } else {
      return "Unexpected response from Hugging Face API.";
    }
  } catch (error) {
    console.error("❌ API Error:", error.message);
    return "❌ Error connecting to Hugging Face API.";
  }
};

// Generate AI Business Report
app.get("/business-report", async (req, res) => {
  const report = await chatbotResponse(
    "Generate a weekly financial report with revenue, expenses, and insights."
  );
  res.json({ report });
});

// AI Chat Endpoint
app.post("/ask-ai", async (req, res) => {
  const userMessage = req.body.message;
  if (!userMessage) {
    return res.status(400).json({ error: "Message is required." });
  }

  const response = await chatbotResponse(userMessage);
  res.json({ response });
});

// Start the Server
const PORT = process.env.PORT || 5000;
app.listen(PORT, () => console.log(`🚀 Server running on port ${PORT}`));

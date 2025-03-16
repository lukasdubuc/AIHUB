import express from "express";
import axios from "axios";
import dotenv from "dotenv";
import fs from "fs";
import path from "path";
import { execSync } from "child_process"; // To run Git commands
import { fileURLToPath } from "url";

dotenv.config();

const app = express();
app.use(express.json());

// Define file paths for ES Modules
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Load API key from Replit Secrets
const HF_API_KEY = process.env.HF_API_KEY || "";

if (!HF_API_KEY) {
    console.error("❌ No Hugging Face API key found in Secrets!");
    process.exit(1);
}

// GitHub Auto-Sync Function (Pull GitHub content)
const autoPullGitHub = () => {
    try {
        console.log("🚀 Pulling latest changes from GitHub...");
        execSync("git pull origin main --no-rebase", { stdio: "inherit" });
        console.log("✅ GitHub pull complete.");
    } catch (error) {
        console.error("❌ Git Pull Failed:", error.message);
    }
};

// AI Chatbot Response
const chatbotResponse = async (userInput) => {
    if (!HF_API_KEY) return "❌ No Hugging Face API key provided.";

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
        return response.data?.generated_text || "Unexpected response from API.";
    } catch (error) {
        console.error("❌ API Error:", error.message);
        return "❌ Error connecting to Hugging Face API.";
    }
};

// Serve Static HTML Page
const htmlFilePath = path.join(__dirname, "index.html");

app.get("/", (req, res) => {
    res.sendFile(htmlFilePath);
});

// AI Business Report
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

// GitHub Pull Endpoint
app.get("/sync-github", (req, res) => {
    console.log("🚀 Syncing with GitHub...");
    autoPullGitHub();
    res.json({ message: "GitHub content synced successfully!" });
});

// Start the server
const PORT = process.env.PORT || 5000;
const HOST = "0.0.0.0";
app.listen(PORT, HOST, () => console.log(`🚀 Server running on http://${HOST}:${PORT}`));

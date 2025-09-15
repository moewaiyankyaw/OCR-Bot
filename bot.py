import telebot
import requests
import base64
import io
import os
from flask import Flask

# === CONFIGURATION from Environment Variables ===
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "8235129652:AAF8iQBtohRglzC_ZiXIpK04RnS5faXTZWg")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "AIzaSyCqPjYMV1FYaoxmyj49oFc93k356CxWZkI")

# Gemini API endpoint
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"

# Initialize bot
bot = telebot.TeleBot(TELEGRAM_TOKEN)

# Initialize Flask
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is alive and running on Render! 🚀"

@app.route('/ping')
def ping():
    return "Pong! Bot is up!", 200

# Run Flask in a separate thread
def run_flask():
    port = int(os.getenv("PORT", 10000))  # Render sets $PORT, fallback to 10000
    app.run(host="0.0.0.0", port=port)

# === Telegram Bot Functions ===
def extract_text_with_gemini(image_bytes):
    try:
        base64_image = base64.b64encode(image_bytes).decode("utf-8")

        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": GEMINI_API_KEY
        }

        payload = {
            "contents": [
                {
                    "parts": [
                        {
                            "inline_data": {
                                "mime_type": "image/jpeg",
                                "data": base64_image
                            }
                        },
                        {
                            "text": "Extract all visible text. If there are math equations, formulas, numbers, or symbols, highlight them clearly. And I want to rearrange and format beautified to the maths expression. And I want to also allow for Burmese Language."
                        }
                    ]
                }
            ]
        }

        response = requests.post(GEMINI_URL, headers=headers, json=payload)

        if response.status_code == 200:
            result = response.json()
            return result["candidates"][0]["content"]["parts"][0]["text"]
        else:
            return f"❌ Gemini API Error: {response.status_code}\n{response.text[:200]}"
    except Exception as e:
        return f"❌ Processing failed: {str(e)}"

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "📸 Send me an image! I'll extract text (especially math) using AI — no files saved!")

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    try:
        file_info = bot.get_file(message.photo[-1].file_id)
        image_bytes = bot.download_file(file_info.file_path)

        sent_msg = bot.reply_to(message, "🔍 Extracting text from image...")

        extracted_text = extract_text_with_gemini(image_bytes)

        bot.edit_message_text(
            chat_id=sent_msg.chat.id,
            message_id=sent_msg.message_id,
            text="✅ Extracted Text:\n\n" + extracted_text
        )
    except Exception as e:
        bot.reply_to(message, f"❌ Failed to process image: {str(e)}")

@bot.message_handler(func=lambda message: True)
def fallback(message):
    bot.reply_to(message, "Please send an image, not text.")

# === Start Everything ===
if __name__ == "__main__":
    from threading import Thread

    # Start Flask in a background thread
    thread = Thread(target=run_flask)
    thread.daemon = True
    thread.start()

    # Start Telegram bot polling
    print("Bot is running with Flask on 0.0.0.0:10000...")
    bot.polling(none_stop=True, timeout=60)

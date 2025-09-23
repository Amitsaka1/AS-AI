import os
import telegram
from flask import Flask, request
import asyncio
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ParseMode

# Logging को सेटअप करना
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# टोकन को लोड करना
TOKEN = os.environ.get('TELEGRAM_TOKEN')
if not TOKEN:
    logger.error("TELEGRAM_TOKEN एनवायरनमेंट वेरिएबल नहीं मिला!")

# ==================================================
# AI का नियम-आधारित दिमाग (यह वही रहेगा)
# ==================================================
def get_ai_response(user_command):
    command = user_command.lower()
    if 'heading' in command:
        return "<h1></h1>"
    elif 'paragraph' in command:
        return "<p></p>"
    elif 'link' in command:
        return "<a href=''></a>"
    else:
        return "कमांड समझ नहीं आई। 'heading', 'paragraph', या 'link' ट्राई करें।"

# ==================================================
# टेलीग्राम कमांड हैंडलर्स
# ==================================================
# /start कमांड के लिए
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("नमस्ते! मैं आपका HTML बॉट हूँ। मुझे कोई कमांड दें।")

# किसी भी टेक्स्ट मैसेज के लिए
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    logger.info(f"'{update.effective_chat.id}' से मैसेज आया: '{user_text}'")
    
    # AI से जवाब पाना
    ai_response = get_ai_response(user_text)
    
    # यूज़र को जवाब भेजना
    await update.message.reply_text(f"Generated Code:\n`{ai_response}`", parse_mode=ParseMode.MARKDOWN)

# ==================================================
# Flask वेब एप्लीकेशन और बॉट का सेटअप
# ==================================================
app = Flask(__name__)
application = Application.builder().token(TOKEN).build()

# कमांड्स को उनके फंक्शन से जोड़ना
application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

@app.route(f'/{TOKEN}', methods=['POST'])
def respond():
    # टेलीग्राम से आने वाले अपडेट को प्रोसेस करना
    asyncio.run(application.update_queue.put(Update.de_json(request.get_json(force=True), application.bot)))
    return 'ok'

@app.route('/setwebhook')
def set_webhook():
    host_url = request.url_root.replace("http://", "https://")
    webhook_url = f'{host_url}{TOKEN}'
    asyncio.run(application.bot.set_webhook(webhook_url))
    return f"Webhook setup ok for {webhook_url}"

@app.route('/')
def index():
    return 'Server is running...'

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
    

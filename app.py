import os
import telegram
from flask import Flask, request
import asyncio
import logging
from telegram.constants import ParseMode # --- 1. यहाँ बदलाव किया गया है ---

# Logging को सेटअप करना
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# टोकन को लोड करना
TOKEN = os.environ.get('TELEGRAM_TOKEN')
if not TOKEN:
    logger.error("TELEGRAM_TOKEN एनवायरनमेंट वेरिएबल नहीं मिला!")

bot = telegram.Bot(token=TOKEN)
app = Flask(__name__)

# AI का नियम-आधारित दिमाग
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

# यह URL टेलीग्राम से मैसेज रिसीव करेगा
@app.route(f'/{TOKEN}', methods=['POST'])
def respond():
    try:
        update = telegram.Update.de_json(request.get_json(force=True), bot)
        if update.message and update.message.text:
            chat_id = update.message.chat.id
            user_text = update.message.text
            logger.info(f"'{chat_id}' से मैसेज आया: '{user_text}'")
            ai_response = get_ai_response(user_text)
            
            # --- 2. यहाँ बदलाव किया गया है ---
            asyncio.run(bot.sendMessage(chat_id=chat_id, text=f"Generated Code:\n`{ai_response}`", parse_mode=ParseMode.MARKDOWN))
    except Exception as e:
        logger.error(f"एक एरर आई: {e}", exc_info=True)
    return 'ok'

# यह URL वेबहुक सेट करने के लिए है
@app.route('/setwebhook')
def set_webhook():
    host_url = request.url_root.replace("http://", "https://")
    webhook_url = f'{host_url}{TOKEN}'
    
    s = asyncio.run(bot.setWebhook(webhook_url))
    message = "Webhook setup ok" if s else "Webhook setup failed"
    logger.info(message)
    return message

@app.route('/')
def index():
    return 'Server is running...'

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
    

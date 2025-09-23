import os
import telegram
from flask import Flask, request

# टोकन को सुरक्षित जगह से लोड करना
TOKEN = os.environ.get('TELEGRAM_TOKEN')
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
    update = telegram.Update.de_json(request.get_json(force=True), bot)
    chat_id = update.message.chat.id
    user_text = update.message.text

    # AI से जवाब पाना
    ai_response = get_ai_response(user_text)

    # यूज़र को जवाब भेजना
    bot.sendMessage(chat_id=chat_id, text=f"Generated Code:\n`{ai_response}`", parse_mode=telegram.ParseMode.MARKDOWN)
    return 'ok'

# यह URL वेबहुक सेट करने के लिए है
@app.route('/setwebhook')
def set_webhook():
    host_url = request.url_root
    webhook_url = f'{host_url}{TOKEN}'
    s = bot.setWebhook(webhook_url)
    return "Webhook setup ok" if s else "Webhook setup failed"

@app.route('/')
def index():
    return 'Server is running...'

if __name__ == '__main__':
    app.run(threaded=True)
  

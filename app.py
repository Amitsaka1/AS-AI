import os
import torch
import asyncio
import logging
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ParseMode
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
from peft import PeftModel

# Logging सेटअप
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ================================================================
# 1. कॉन्फ़िगरेशन (Configuration)
# ================================================================
TOKEN = os.environ.get('TELEGRAM_TOKEN')
if not TOKEN:
    logger.error("TELEGRAM_TOKEN एनवायरनमेंट वेरिएबल नहीं मिला!")

# Hugging Face पर आपके ट्रेन किए हुए मॉडल का नाम
BASE_MODEL_ID = "google/gemma-7b"
ADAPTER_MODEL_ID = "Amitsaka1/gemma-7b-coding-assistant" # <--- यह आपका ट्रेन किया हुआ मॉडल है

# ================================================================
# 2. AI मॉडल और टोकनाइज़र लोड करना
# ================================================================
print("🧠 AI का दिमाग (Gemma 7B + Your Brain) लोड किया जा रहा है...")
try:
    # QLoRA के लिए कॉन्फ़िगरेशन
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16
    )
    
    # बेस मॉडल (Gemma 7B) लोड करना
    base_model = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL_ID,
        quantization_config=bnb_config,
        device_map="auto"
    )
    
    # टोकनाइज़र लोड करना
    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL_ID)
    tokenizer.pad_token = tokenizer.eos_token
    
    # आपके ट्रेन किए हुए 'स्किल चिप्स' (LoRA Adapters) को बेस मॉडल के साथ मिलाना
    model = PeftModel.from_pretrained(base_model, ADAPTER_MODEL_ID)
    
    print("✅ AI का दिमाग सफलतापूर्वक लोड हो गया है!")
except Exception as e:
    logger.error(f"मॉडल लोड करने में त्रुटि: {e}")
    model = None

# ================================================================
# 3. AI से सवाल पूछने का फंक्शन
# ================================================================
async def ask_ai(prompt):
    if not model:
        return "माफ कीजिए, AI मॉडल अभी तैयार नहीं है।"
    
    # प्रॉम्प्ट को सही फॉर्मेट में बदलना
    full_prompt = f"### Instruction:\n{prompt}\n\n### Response:\n"
    
    # टेक्स्ट को नंबर्स (टोकन्स) में बदलना
    inputs = tokenizer(full_prompt, return_tensors="pt").to("cuda")
    
    # AI से जवाब जेनरेट करवाना
    outputs = model.generate(**inputs, max_new_tokens=256)
    
    # जवाब को वापस टेक्स्ट में बदलना
    response_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
    
    # सिर्फ AI का जवाब वाला हिस्सा निकालना
    return response_text.split("### Response:")[1].strip()

# ================================================================
# 4. टेलीग्राम हैंडलर्स
# ================================================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("नमस्ते! मैं आपका फाइन-ट्यून किया हुआ Gemma 7B कोडिंग असिस्टेंट हूँ।")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    chat_id = update.effective_chat.id
    logger.info(f"'{chat_id}' से मैसेज आया: '{user_text}'")
    
    # "सोच रहा हूँ..." मैसेज भेजना
    thinking_message = await update.message.reply_text("🧠 सोच रहा हूँ...")
    
    # AI से जवाब पाना
    ai_response = await ask_ai(user_text)
    
    # "सोच रहा हूँ..." मैसेज को एडिट करके फाइनल जवाब देना
    await context.bot.edit_message_text(chat_id=chat_id, message_id=thinking_message.message_id, text=f"```\n{ai_response}\n```", parse_mode=ParseMode.MARKDOWN_V2)

# ================================================================
# 5. Flask वेब एप्लीकेशन और बॉट का सेटअप
# ================================================================
app = Flask(__name__)
application = Application.builder().token(TOKEN).build()
application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

@app.route(f'/{TOKEN}', methods=['POST'])
def respond():
    asyncio.run(application.process_update(Update.de_json(request.get_json(force=True), application.bot)))
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
    

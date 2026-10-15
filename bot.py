import os
import threading
import telebot
from flask import Flask

# Apna token yahan daal do
TOKEN = "8971897939:AAFK8opTqe11e4zsXQktpsfpK5NIKD3Zu1c"  

bot = telebot.TeleBot(TOKEN)
server = Flask(__name__)

@server.route('/')
def home():
    return "HubStream Bot is alive and running!", 200

@bot.message_handler(commands=['start', 'getpass'])
def send_pass_link(message):
    user_name = message.from_user.first_name or "User"
    
    markup = telebot.types.InlineKeyboardMarkup()
    activate_btn = telebot.types.InlineKeyboardButton(
        "🎬 Click to Activate 24H Pass", 
        url="https://hubstreamofficial.vercel.app/?pass=active"
    )
    markup.add(activate_btn)
    
    response_text = (
        f"👋 Hey *{user_name}*!\n\n"
        f"Your 24-hour movie streaming pass for *HubStream* is ready.\n\n"
        f"👇 Click the button below to unlock your access instantly:"
    )
    
    bot.send_message(
        message.chat.id, 
        response_text, 
        reply_markup=markup, 
        parse_mode="Markdown"
    )

def run_telegram_bot():
    print("🤖 Telegram Bot polling started...")
    bot.infinity_polling()

if __name__ == "__main__":
    # Bot ko background thread mein chala do
    bot_thread = threading.Thread(target=run_telegram_bot)
    bot_thread.daemon = True
    bot_thread.start()
    
    # Render ke liye web server start karo (PORT binding)
    port = int(os.environ.get("PORT", 10000))
    print(f"🌍 Web server running on port {port}...")
    server.run(host="0.0.0.0", port=port)

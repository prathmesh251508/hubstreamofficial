import os
import telebot
from flask import Flask, request
# Yahan "YOUR_BOT_API_TOKEN_HERE" hata kar apna asli BotFather token seedha daal do
TOKEN = "8971897939:AAFK8opTqe11e4zsXQktpsfpK5NIKD3Zu1c"  

bot = telebot.TeleBot(TOKEN)
bot = telebot.TeleBot(TOKEN)
server = Flask(__name__)

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
    bot.send_message(message.chat.id, response_text, reply_markup=markup, parse_mode="Markdown")

@server.route(f"/{TOKEN}", methods=['POST'])
def webhook():
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "!", 200

@server.route("/")
def webhook_info():
    return "HubStream Bot is running!", 200

if __name__ == "__main__":
    # Render khud PORT environment variable assign karta hai
    port = int(os.environ.get('PORT', 5000))
    # Webhook setup kar lo ya polling (agar simple rakhna hai)
    # Render Web Service ke liye polling ki jagah webhook ya background thread use hota hai, 
    # lekin agar polling chalani hai toh Flask ko dummy health-check ke liye rakhte hain.
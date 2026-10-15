import telebot
from telebot import types

# BotFather se mila hua API token yaha dalein
TOKEN = "YOUR_BOT_API_TOKEN_HERE"
bot = telebot.TeleBot(TOKEN)

# Jab bhi koi /start dabaye ya link se aaye
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_name = message.from_user.first_name
    
    # Inline button jo user ko wapas website par le jayega aur pass active karega
    markup = types.InlineKeyboardMarkup()
    activate_btn = types.InlineKeyboardButton(
        "🎬 Activate 24H Pass Now", 
        url="https://hubstreamofficial.vercel.app/?pass=active"
    )
    markup.add(activate_btn)
    
    welcome_text = (
        f"👋 Hello *{user_name}*!\n\n"
        f"Welcome to *HubStream* Access Bot.\n"
        f"Click the button below to instantly unlock your 24-hour movie streaming pass on the website:"
    )
    
    bot.send_message(
        message.chat.id, 
        welcome_text, 
        reply_markup=markup, 
        parse_mode="Markdown"
    )

if __name__ == "__main__":
    print("Bot is running...")
    bot.infinity_polling()
import telebot
from misck import token, chat_id_old

# Вставьте ваш токен бота
#TOKEN = "ВАШ_ТОКЕН_БОТА"
bot = telebot.TeleBot(token)

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, f"Ваш chat_id: {message.chat.id}")

@bot.message_handler(func=lambda message: True)
def echo_all(message):
    bot.reply_to(message, f"Ваш chat_id: {message.chat.id}")

print("Бот запущен. Напишите ему любое сообщение.")
bot.polling()
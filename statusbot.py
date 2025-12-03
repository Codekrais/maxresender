import telebot
from dotenv import load_dotenv
import os

load_dotenv()
token = os.getenv("TG_BOT_TOKEN")
bot = telebot.TeleBot(token)

def poll():
    while True:
        try:
            @bot.message_handler(commands=['f'])
            def wc(message):
                bot.send_message(message.chat.id, 'Бот активен')

            @bot.message_handler(commands=['start'])
            def wc(message):
                bot.send_message(message.chat.id, '''<b>MAX RESENDER BY KRAIS</b>
                
Бот, пересылающий сообщения из мессенджера MAX в телеграм

Бот работает на базе API мессенджера MAX и отправки запросов .json файлом по WEBSOCKETS. Написан на языке PYTHON

<U>Версия: 0.3 beta от 14.11.25</U>

Разработчик текущей версии: <i>@endurra</i>

Процесс разработки и полезная информация: <i>@codebykrais</i>
                    ''', parse_mode='HTML')
        except: pass

        while True:
            try:
                bot.polling(non_stop=True)
            except:
                break
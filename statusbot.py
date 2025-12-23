#НЕ НУЖЕН ДЛЯ ФУНКЦИОНАЛА
# import telebot
# from dotenv import load_dotenv
# import os
#
# load_dotenv()
# token = os.getenv("TG_BOT_TOKEN")
# bot = telebot.TeleBot(token)
#
# def poll():
#     @bot.message_handler(commands=['f'])
#     def status(message):
#         try:
#             bot.send_message(message.chat.id, 'Бот активен')
#         except: print("Ошибка отправки")
#
#     @bot.message_handler(commands=['start'])
#     def start(message):
#         try:
#             bot.send_message(message.chat.id, '''<b>MAX RESENDER BY KRAIS</b>
#
# Бот, пересылающий сообщения из мессенджера MAX в телеграм
#
# Бот работает на базе API мессенджера MAX и отправки запросов .json файлом по WEBSOCKETS. Написан на языке PYTHON
#
# <U>Версия: 0.4 beta от 3.12.25</U>
#
# Разработчик текущей версии: <i>@endurra</i>
#
# Процесс разработки и полезная информация: <i>@codebykrais</i>
#             ''', parse_mode='HTML')
#         except: print("Ошибка отправки")
#
#     @bot.message_handler(commands=['send'])
#     def send(message):
#         print("Вход в функцию")
#         try:
#             print("Обработка сообщения")
#             argument_list = message.text.split(" ")
#             chat_id = int(argument_list[1])
#             print(chat_id)
#             message_body = " ".join(argument_list[2::])
#             print(message_body)
#         except Exception as e: print(f"Ошибка: {e}")
#
#
#     while True:
#         try:
#             bot.polling(non_stop=True)
#         except:
#             print("Ошибка")
#             pass
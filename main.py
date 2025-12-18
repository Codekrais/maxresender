from max import MaxClient as Client
from filters import filters
from classes import Message
from telegram import send_to_telegram
import time, os
from dotenv import load_dotenv
import telebot
import os


load_dotenv()
MAX_TOKEN = os.getenv("MAX_TOKEN")
MAX_CHAT_IDS = [int(x) for x in os.getenv("MAX_CHAT_IDS").split(",")]

TG_BOT_TOKEN = os.getenv("TG_BOT_TOKEN")
TG_CHAT_ID = os.getenv("TG_CHAT_ID")
TG_ADMIN_ID = os.getenv("TG_ADMIN_ID")
bot = telebot.TeleBot(TG_BOT_TOKEN)



if MAX_TOKEN == "" or MAX_CHAT_IDS == [] or TG_BOT_TOKEN == "" or TG_CHAT_ID == "":
    print("Ошибка в .env, перепроверьтье")
MONITOR_ID = os.getenv("MONITOR_ID")

client = Client(MAX_TOKEN)

@client.on_connect
def onconnect():
    if client.me != None:
        print(f'[{client.current_time()}] Имя: {client.me.contact.names[0].name}, Номер: {client.me.contact.phone} | ID: {client.me.contact.id}\n')


@client.on_message(filters.any())
def onmessage(client: Client, message: Message):
    forward = None
    link = False
    if message.chat.id in MAX_CHAT_IDS:
        msg_text = message.text
        msg_attaches = message.attaches
        name = message.user.contact.names[0].first_name + ' ' + message.user.contact.names[0].last_name
        if "link" in message.kwargs.keys():
            if "type" in message.kwargs["link"]:
                if message.kwargs["link"]["type"] == "REPLY":  # TODO
                    ...
                if message.kwargs["link"]["type"] == "FORWARD":
                    msg_text = message.kwargs["link"]["message"]["text"]
                    msg_attaches = message.kwargs["link"]["message"]["attaches"]
                    forwarded_msg_author = client.get_user(id=message.kwargs["link"]["message"]["sender"], _f=1)
                    forward = f"<U>переслал(а) сообщение от:</U> {forwarded_msg_author.contact.names[0].first_name} {forwarded_msg_author.contact.names[0].last_name}"
                    link = True

        if msg_text != "" or msg_attaches != []:
            not_forward = f'<U>отправил(а) сообщение:</U>'
            match message.status:
                case "REMOVED":
                    send_to_telegram(
                        TG_BOT_TOKEN,
                        TG_CHAT_ID,
                        f"<b>Из чата \"{message.chatname}\"</b>:\n\n<b>{name}</b> <U>Удалил(а) сообщение:</U>\n\n{msg_text if msg_text != "" else ''}{f'Файл по ссылке: {message.url}'if message.url else ''}",
                        [attach['baseUrl'] for attach in msg_attaches if 'baseUrl' in attach], type=message._type, file_url=message.url)
                case "EDITED":
                    edited = 'изменил(а) сообщение:\n\n'
                    send_to_telegram(
                        TG_BOT_TOKEN,
                        TG_CHAT_ID,
                        f"<b>Из чата \"{message.chatname}\"</b>:\n\n<b>{name}</b> <U>{edited}</U>{msg_text if msg_text != "" else ''}{f'Файл по ссылке: {message.url}'if message.url else ''}",
                        [attach['baseUrl'] for attach in msg_attaches if 'baseUrl' in attach], type=message._type, file_url=message.url)
                case _:
                    send_to_telegram(
                        TG_BOT_TOKEN,
                        TG_CHAT_ID,
                        f"<b>Из чата \"{message.chatname}\"</b>:\n\n<b>{name}</b> {forward if link else not_forward}\n\n{msg_text if msg_text != "" else ''}{f'Файл по ссылке: {message.url}'if message.url else ''}",
                        [attach['baseUrl'] for attach in msg_attaches if 'baseUrl' in attach], type=message._type, file_url=message.url)

def status_bot():
    @bot.message_handler(commands=['f'])
    def status(message):
        try:
            bot.send_message(message.chat.id, 'Бот активен')
        except Exception as e:
            bot.send_message(message.chat.id, f"Ошибка: {e}")

    @bot.message_handler(commands=['start'])
    def start(message):
        try:
            bot.send_message(message.chat.id, '''<b>MAX RESENDER BY KRAIS</b>

Бот, пересылающий сообщения из мессенджера MAX в телеграм

Бот работает на базе API мессенджера MAX и отправки запросов .json файлом по WEBSOCKETS. Написан на языке PYTHON

<U>Версия: 0.4 beta от 3.12.25</U>

Разработчик текущей версии: <i>@endurra</i>

Процесс разработки и полезная информация: <i>@codebykrais</i>
            ''', parse_mode='HTML')
        except Exception as e:
            bot.send_message(message.chat.id, f"Ошибка: {e}")

    @bot.message_handler(commands=['send'])
    def send(message):
        try: #Общий обработчки ошибок
            if str(message.from_user.id) == TG_ADMIN_ID: #Проверка по id

                argument_list = message.text.split(" ")
                max_chat_id = argument_list[1]
                print(max_chat_id, type(max_chat_id))
                message_body = " ".join(argument_list[2::]) #Текст после /send

                if message_body and max_chat_id: #Если текст не пустой
                    recv = client.send_message(chat_id=int(max_chat_id), text=message_body) #Отправка сообщения
                    bot.send_message(message.chat.id, recv)
                else: bot.send_message(message.chat.id, "Вы не ввели id или сообщение после /send")#Если текст пустой
            else: bot.send_message(message.chat.id, "Вы не можете воспользоваться данной командой!")#Если id не совпал

        except Exception as e: #Except общего обработчика
            bot.send_message(message.chat.id, f"Ошибка: {e}")

    while True:
        try:
            bot.polling(non_stop=True)
        except:
            print("Ошибка")
            pass


if __name__ == "__main__":
    client.run()
    status_bot()




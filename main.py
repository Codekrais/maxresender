from max import MaxClient as Client
from max_bot import MaxClientBot as Client_bot
from filters import filters, user
from classes import Message, get_chatlist
from telegram import send_to_telegram
import asyncio
import aiohttp
import os
import json
from datetime import datetime, timedelta, timezone
import telebot
from telebot.async_telebot import AsyncTeleBot


# Removed deprecated event loop policy setting for Python 3.14+

load_dotenv = lambda: __import__('dotenv').load_dotenv()
load_dotenv()

MAX_TOKEN = os.getenv("MAX_TOKEN")
MAX_CHAT_IDS = [int(x) for x in os.getenv("MAX_CHAT_IDS").split(",")]

TG_BOT_TOKEN = os.getenv("TG_BOT_TOKEN")
TG_CHAT_ID = os.getenv("TG_CHAT_ID")
TG_ADMIN_ID = [x for x in os.getenv("TG_ADMIN_ID").split(",")]
bot = AsyncTeleBot(TG_BOT_TOKEN, parse_mode="HTML")


if MAX_TOKEN == "" or MAX_CHAT_IDS == [] or TG_BOT_TOKEN == "" or TG_CHAT_ID == "":
    print("Ошибка в .env, перепроверьте")
MONITOR_ID = os.getenv("MONITOR_ID")

client = Client(MAX_TOKEN)
client_bot = Client_bot(MAX_TOKEN)


def check_file_type(message: Message) -> str:
    match message._type:
        case "VIDEO": return f'<b>🪛 Необработанные файлы:</b> Видеофайл'
        case "AUDIO": return f'<b>🪛 Необработанные файлы:</b> Аудиофайл'
        case _: return ""


def get_forward_usr_name(message: Message) -> str:
    match message.forward_type:
        case "USER":
            return client.get_user(id=message.kwargs["link"]["message"]["sender"], _f=1).contact.names[0].name
        case "CHANNEL":
            return message.kwargs["link"]["chatName"]


def get_usr_name(message: Message) -> str:
    match message.type:
        case "USER":
            return message.user.contact.names[0].name
        case "CHANNEL":
            return "Администратор канала"


def get_chatname(message: Message) -> str:
    match message.type:
        case "USER":
            return f"<b>💬 Из чата \"{message.chatname}\"</b>:"
        case "CHANNEL":
            return f"<b>💬 Из канала \"{message.chatname}\"</b>:"


def get_file_url(message: Message) -> str:
    if message.url:
        return f'\n<b>🔗 Файл по ссылке:</b> {message.url}\n'
    else:
        return ""


@client.on_connect
async def onconnect():
    if client.me is not None:
        print(f'[{client.current_time()}] Имя: {client.me.contact.names[0].name}, Номер: {client.me.contact.phone} | ID: {client.me.contact.id}\n')


@client.on_message(filters.any())
async def onmessage(client: Client, message: Message):
    forward = None
    link = False
    if message.chat.id in MAX_CHAT_IDS:
        msg_text = message.text
        msg_attaches = message.attaches
        name = get_usr_name(message)
        if "link" in message.kwargs.keys():
            if "type" in message.kwargs["link"]:
                if message.kwargs["link"]["type"] == "REPLY":
                    ...
                if message.kwargs["link"]["type"] == "FORWARD":
                    msg_text = message.kwargs["link"]["message"]["text"]
                    msg_attaches = message.kwargs["link"]["message"]["attaches"]
                    forwarded_msg_author = get_forward_usr_name(message)
                    forward = f"♻️ <U>Переслал(а) сообщение от:</U> 👤 {forwarded_msg_author}"
                    link = True

        if msg_text != "" or msg_attaches != []:
            async with aiohttp.ClientSession() as session:
                match message.status:
                    case "REMOVED":
                        await send_to_telegram(session,
                            TG_BOT_TOKEN,
                            TG_CHAT_ID,
                            f"""
{get_chatname(message)}

<b>👤 {name}</b> ❌ <U>Удалил(а) сообщение:</U>

<b>📜 Сообщение:</b> {msg_text}
{get_file_url(message)}
{check_file_type(message)}""",
                            [attach['baseUrl'] for attach in msg_attaches if 'baseUrl' in attach])
                    case "EDITED":
                        await send_to_telegram(session,
                            TG_BOT_TOKEN,
                            TG_CHAT_ID,
                            f"""
{get_chatname(message)}

<b>👤 {name}</b> ✒️ <U>Изменил(а) сообщение:</U>

<b>📜 Сообщение:</b> {msg_text}
{get_file_url(message)}
{check_file_type(message)}""",
                            [attach['baseUrl'] for attach in msg_attaches if 'baseUrl' in attach])
                    case _:
                        await send_to_telegram(session,
                            TG_BOT_TOKEN,
                            TG_CHAT_ID,
                            f"""
{get_chatname(message)}

<b>👤 {name}</b> {forward if link else '📨 <U>Отправил(а) сообщение:</U>'}

<b>📜 Сообщение:</b> {msg_text}
{get_file_url(message)}
{check_file_type(message)}""",
                            [attach['baseUrl'] for attach in msg_attaches if 'baseUrl' in attach])


async def status_bot():
    # ---Обработчики--
    def errorHandler(func):
        async def wrapper(message):
            try:
                await func(message)
            except Exception as e:
                await client_bot.disconnect()
                await bot.send_message(message.chat.id, f"Ошибка: {e}❌")
        return wrapper

    def isAdmin(func):
        async def wrapper(message):
            global TG_ADMIN_ID
            if str(message.from_user.id) in TG_ADMIN_ID:
                await func(message)
            else:
                await bot.send_message(message.chat.id, "Вы не можете воспользоваться данной командой!❌")
        return wrapper

    def fstub(func):  # заглушка
        async def wrapper(message):
            if 1 == 1:
                await bot.send_message(message.chat.id, f"Функция на стадии разработки⏳")
        return wrapper

    # ---Конец обработчиков---

    @bot.message_handler(commands=['status'])
    @errorHandler
    async def status(message):
        await bot.send_message(message.chat.id, 'Бот активен✅️')

    @bot.message_handler(commands=['start'])
    @errorHandler
    async def start(message):
        await bot.send_message(message.chat.id, '''<b>MAX RESENDER BY KRAIS</b>

Бот, пересылающий сообщения из мессенджера MAX в телеграм

Бот работает на базе API мессенджера MAX и отправки запросов .json файлом по WEBSOCKETS. Написан на языке PYTHON

<U>Версия: 0.9 beta от 15.02.26</U>

Чтобы увидеть список команд,
введите /com

Разработчик текущей версии: <i>@endurra</i>

Процесс разработки и полезная информация: <i>@codebykrais</i>
            ''', parse_mode='HTML')

    @bot.message_handler(commands=['send'])
    @errorHandler
    @isAdmin
    async def send(message):
        argument_list = message.text.split(" ")  # Парсинг сообщения
        if len(argument_list) < 3:
            await bot.send_message(message.chat.id, "Вы не ввели id или сообщение после /send❌")
        else:
            max_chat_id = argument_list[1]
            message_body = " ".join(argument_list[2::])  # Текст после /send

            match int(max_chat_id):
                case 0:
                    await bot.send_message(message.chat.id, "Отправка сообщения в этот чат невозможна!❌")
                case _:
                    await client_bot.run()
                    recv = await client_bot.send_message(chat_id=int(max_chat_id), text=message_body)
                    # Отправка сообщения
                    if not recv:
                        name = await client_bot.get_chats(id=int(max_chat_id))
                        await bot.send_message(message.chat.id, f'Сообщение в чат <b>"{name.upper()}"</b> было успешно отправлено✅')
                    else:
                        await bot.send_message(message.chat.id, f"При отправке сообщения произошла ошибка: {recv}❌")

                    await client_bot.disconnect()

    @bot.message_handler(commands=['com'])
    @errorHandler
    async def com(message):
        await bot.send_message(message.chat.id, """
/start - стартовое сообщение

/status - статус бота

/send {чат-id чата из MAX} {Сообщение (только текст)} - ДОСТУПНО ТОЛЬКО АДМИНАМ отправить сообщение в чат MAX по чат-id

/com - список команд

/lschat - ДОСТУПНО ТОЛЬКО АДМИНАМ список обработанных чатов

/pin - ДОСТУПНО ТОЛЬКО АДМИНАМ включить/отключить закрепление сообщений ботом

/max_id {номер телефона} - ДОСТУПНО ТОЛЬКО АДМИНАМ получить чат-id из MAX по номеру телефона
        """)

    @bot.message_handler(commands=['lschat'])
    @errorHandler
    @isAdmin
    async def ls(message):
        ls = get_chatlist()
        if ls:
            await bot.send_message(message.chat.id, f"""<b>СПИСОК ОБРАБОТАННЫХ ЧАТОВ:</b>

{ls}""")
        else:
            await bot.send_message(message.chat.id, f"Список обработанных чатов пуст!❌")

    @bot.message_handler(commands=['pin'])
    @errorHandler
    @isAdmin
    async def pin(message):
        with open('config.json', encoding='UTF-8') as f:
            data = json.load(f)
        if data["pin"] == "True":
            data["pin"] = "False"
            await bot.send_message(message.chat.id, f"""Закрепление сообщений отключено!❌""")
        else:
            data["pin"] = "True"
            await bot.send_message(message.chat.id, f"""Закрепление сообщений включено!✅""")
        with open('config.json', 'w', encoding='UTF-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    @bot.message_handler(commands=['max_id'])
    @errorHandler
    @isAdmin
    async def max_id(message):
        message_body = message.text.split()
        if len(message_body) == 2:
            phone = message_body[1]
            await client_bot.run()
            recv = await client_bot.get_user(phone=int(phone))
            if recv:
                res = f"""<b>ПОЛЬЗОВАТЕЛЬ</b> {recv.contact.names[0].name}
<b>CHAT_ID</b> <code>{recv.chat.id}</code>
<b>ДАТА РЕГИСТРАЦИИ</b> {datetime.fromtimestamp(recv.contact.registrationTime / 1000.0, tz=timezone(timedelta(hours=0))).strftime('%d-%m-%Y %H:%M:%S')}"""

                await bot.send_message(message.chat.id, res)
            else:
                await bot.send_message(message.chat.id, "Аккаунт по номеру телефона не найден⛔")
            await client_bot.disconnect()
        else:
            await bot.send_message(message.chat.id, "Вы не ввели номер‼️")

    while True:
        try:
            await bot.delete_webhook(drop_pending_updates=True)
            await bot.polling(non_stop=True)
        except:
            print("Ошибка статус-бота")
            await asyncio.sleep(10)
            pass


async def main():
    # Запускаем клиента и статус-бота параллельно
    await asyncio.gather(
        client.run(),
        status_bot()
    )


if __name__ == "__main__":
    asyncio.run(main())

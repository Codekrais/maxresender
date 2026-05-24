import asyncio
import aiohttp
import json

async def send_to_telegram(session: aiohttp.ClientSession, TG_BOT_TOKEN: str="", TG_CHAT_ID: int = 0, caption: str = "", attachments: list[str] = []):
    if not attachments:  # нет фоток — просто текст
        if caption == "": return
        api_url = f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage"
        async with session.post(api_url, data={
            "chat_id": TG_CHAT_ID,
            "text": caption,
            "parse_mode": "HTML"
            }) as resp:
            result = await resp.json()
            if get_pin():
                message_id = result['result']['message_id']
                pin_url = f"https://api.telegram.org/bot{TG_BOT_TOKEN}/pinChatMessage"
                async with session.post(pin_url, data={
                    "chat_id": TG_CHAT_ID,
                    "message_id": message_id,
                    "disable_notification": True
                }) as pin_resp:
                    pass
            print(f'ПРИНЯТЫЙ ПАКЕТ TG\n{result}\n')
        return

    # одна фотка — отправляем через sendPhoto
    if len(attachments) == 1:
        api_url = f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendPhoto"
        async with session.post(api_url, data={
            "chat_id": TG_CHAT_ID,
            "photo": attachments[0],
            "caption": caption,
            "parse_mode": "HTML"
        }) as resp:
            result = await resp.json()
            if get_pin():
                message_id = result['result']['message_id']
                pin_url = f"https://api.telegram.org/bot{TG_BOT_TOKEN}/pinChatMessage"
                async with session.post(pin_url, data={
                    "chat_id": TG_CHAT_ID,
                    "message_id": message_id,
                    "disable_notification": True
                }) as pin_resp:
                    pass
            print(f'ПРИНЯТЫЙ ПАКЕТ TG\n{result}\n')
        return

    # несколько фоток (от 2 до 10) — альбом
    if 2 <= len(attachments) <= 10:
        api_url = f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMediaGroup"
        media = []
        for i, url in enumerate(attachments):
            item = {"type": "photo", "media": url}
            if i == 0 and caption:
                item["caption"] = caption
                item["parse_mode"] = "HTML"
            media.append(item)


        payload = {
            "chat_id": TG_CHAT_ID,
            "media": json.dumps(media),

        }
        async with session.post(api_url, data=payload) as resp:
            result = await resp.json()
            print(f'ПРИНЯТЫЙ ПАКЕТ TG\n{result}\n')
            if get_pin():
                message_id = result['result'][0]['message_id']
                pin_url = f"https://api.telegram.org/bot{TG_BOT_TOKEN}/pinChatMessage"
                async with session.post(pin_url, data={
                    "chat_id": TG_CHAT_ID,
                    "message_id": message_id,
                    "disable_notification": True
                }) as pin_resp:
                    pass
        return

    # если фоток больше 10 — разобьём на несколько альбомов
    for i in range(0, len(attachments), 10):
        chunk = attachments[i:i+10]
        await send_to_telegram(session, TG_BOT_TOKEN, TG_CHAT_ID, caption if i == 0 else "", chunk)

def get_pin():
    with open('config.json', encoding='UTF-8') as f:
        data = json.load(f)
    if data["pin"] == "True":
        return True
    return False

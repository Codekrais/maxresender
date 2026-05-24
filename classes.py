import json
import time
import asyncio
from typing import Literal

EMOJIS = Literal[
    '❤️','👍','🤣','🔥','💯','😍','🎉','⚡',
    '🤩','🤘','😎','🙄','😐','😁','🤪','😉',
    '🤤','😇','😘','🥰','🥳','🌚','🌝','😴',
    '🫠','🤔','🫡','😳','🥱','🐈','🐶','💪',
    '🤞','👋','👏','🤝','👌','🙏','💋','👑',
    '⭐','🍷','🍑','🤷‍♀️','🤷‍♂️','👩‍❤️‍👨','🦄','👻',
    '🗿','👀','👁️','🖤','❤️‍🩹','🛑','⛄','❓',
    '❗️'
]


def get_chatlist():
    with open('chatlist.json', encoding='UTF-8') as f:
        data = json.load(f)
    res = ""
    for chat_id, name in data.items():
        res += f"{name}: <code>{chat_id}</code>\n\n"
    return res


class Name:
    def __init__(self, name='', firstName='', lastName='', type=''):
        self.first_name = firstName
        self.last_name = lastName
        self.type = type
        self.name = f"{firstName} {lastName}".rstrip()


class Contact:
    def __init__(self, client, accountStatus=None, baseUrl=None, names=None, phone=None, description=None,
                 options=None, photoId=None, updateTime=None, id=None, baseRawUrl=None,
                 gender=None, link=None, **kwargs):
        self._client = client
        self.accountStatus = accountStatus
        self.base_url = baseUrl
        self.names = [Name(**n) for n in names]
        self.phone = phone
        self.description = description
        self.options = options
        self.photo_id = photoId
        self.update_time = updateTime
        self.id = id
        self.link = link
        self.gender = gender
        self.base_raw_url = baseRawUrl
        self.registrationTime = kwargs.get("registrationTime")

    async def add(self):
        return await self._client.contact_add(self.id)

    async def remove(self):
        return await self._client.contact_remove(self.id)

    async def block(self):
        return await self._client.contact_block(self.id)

    async def unblock(self):
        return await self._client.contact_unblock(self.id)


class User:
    def __init__(self, client, profile, _f=0):
        self._client = client
        self.contact = Contact(client, **profile)
        _id = client.me.contact.id if client.me else profile["id"]
        if not _f:
            self.chat = Chat(self._client, profile["id"] ^ _id)

        if profile["id"] != _id:
            pass


class Chat:
    def __init__(self, client, chat_id):
        self._client = client
        self.id: int = chat_id
        self.link = f"https://web.max.ru/{chat_id}"
        self.messages: list[Message] = []

    async def _init_messages(self, seq, chat_id):
        if self._client.websocket is None:
            return
        await self._client.websocket.send(json.dumps({
            "ver": 11,
            "cmd": 0,
            "seq": seq,
            "opcode": 49,
            "payload": {
                "chatId": chat_id,
                "from": int(time.time() * 1000),
                "forward": 0,
                "backward": 30,
                "getMessages": True
            }
        }))
        while True:
            r = await self._client.websocket.recv()
            recv = json.loads(r)
            if recv["seq"] == seq and recv["opcode"] == 49:
                break
            else:
                pass

        payload = recv["payload"]
        if not recv["opcode"] in [150]:
            _ = []
            try:
                msg = payload["messages"][-1]
                m = Message(self._client, 0, **msg, _f=1)
                _.append(m)
                self.messages = _
            except IndexError:
                pass

    async def pin(self):
        await self._client.pin_chat(self.id)

    async def unpin(self):
        await self._client.unpin_chat(self.id)

    async def clear_history(self):  # TODO
        pass


class Message:

    def __init__(self, client, chatId: str, sender: str = None, id=None, time=None, text=None, type=None, _f=0,
                 **kwargs):
        self._client = client
        self.kwargs = kwargs
        self.status = kwargs.get("status")

        if not _f:
            self.chat = Chat(client, chatId)
        self.sender = sender
        self.id = id
        self.time = time
        self.text = text
        self.type = type
        self.forward_type = self.kwargs.get("link", {}).get("message", {}).get("type")
        self.update_time = kwargs.get("updateTime")
        self.options = kwargs.get("options")
        self.cid = kwargs.get("cid")
        self.attaches = kwargs.get("attaches", [])
        self.attaches_forward = self.kwargs.get("link", {}).get("message", {}).get("attaches", [])
        self.reaction_info = kwargs.get("reactionInfo", {})
        self.user = client.get_user(id=sender, _f=1) if sender else None
        self.chatname = ""  # Будет заполнено асинхронно позже
        self._type = self.get_ftype()
        self.fileid = self.get_fileid()
        self.url = None  # Будет заполнено асинхронно позже
        if chatId != 0:
            self.add_in_chatlist(chatid=str(chatId), chatname="Unknown")
    
    async def init_async(self):
        """Асинхронная инициализация сообщения"""
        if self.chat.id:
            self.chatname = await self._client.get_chats(self.chat.id)
            self.add_in_chatlist(chatid=str(self.chat.id), chatname=str(self.chatname))
        if self.fileid:
            self.url = await self._client.download_file(chat_id=self.chat.id, message_id=self.id, file_id=self.fileid)

    def add_in_chatlist(self, chatid: str, chatname: str):
        with open('chatlist.json', encoding='UTF-8') as f:
            data = json.load(f)

        data.update({chatid: chatname})

        with open('chatlist.json', 'w', encoding='UTF-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    def get_ftype(self):
        if self.attaches:
            return self.attaches[0].get("_type")
        elif self.attaches_forward:
            return self.attaches_forward[0].get("_type")
        else:
            return None

    def get_fileid(self):
        if self._type == "FILE" and not self.kwargs.get("link"):
            return self.attaches[0].get('fileId')
        elif (self.kwargs.get("link")) and (self.attaches_forward):
            return self.attaches_forward[0].get('fileId')

        elif self._type == "VIDEO" and not self.kwargs.get("link"):
            return self.attaches[0].get('videoId')

        else:
            return None

    async def reply(self, text: str, **kwargs) -> "Message":
        return await self._client.send_message(self.chat.id, text, self.id, **kwargs)

    async def answer(self, text: str, **kwargs) -> "Message":
        return await self._client.send_message(self.chat.id, text, **kwargs)

    async def delete(self, for_me=False):
        return await self._client.delete_message(self.chat.id, [self.id], for_me)

    async def edit(self, text: str) -> "Message":
        return await self._client.edit_message(self.chat.id, self.id, text)

    async def react(self, reaction: EMOJIS) -> "Reactions":
        return await self._client.set_reaction(self.chat.id, self.id, reaction)


class Reaction:
    def __init__(self, reaction: str, count: int):
        self.reaction = reaction
        self.count = count


class Reactions:
    def __init__(self, **kwargs):
        reaction_info = kwargs.get('reactionInfo', {})
        self.counters = [Reaction(**c) for c in reaction_info.get('counters', [])]
        self.your_reaction = reaction_info.get('yourReaction')
        self.total_count = reaction_info.get('totalCount')

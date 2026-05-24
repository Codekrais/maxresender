import asyncio
import websockets
import json
from uuid import uuid4
from classes import *
from errors import *
from datetime import datetime


class MaxClientBot:
    def __init__(self, token: str | None = None, phone: str | None = None):
        self.error = False
        self.id = None

        self._seq = 0

        self.phone_number = phone
        self.auth_token = token
        self.user_agent = self._generate_user_agent()

        self.websocket = None

        self._19_payload = None
        self._on_connect = None
        self._connected = False
        self._t = None
        self._t_stop = False

        self.is_log_in = False
        self.me = None
        self.session_id = int(time.time() * 1000)

        self.handlers = []

    def current_time(self):
        current_time = datetime.now()
        return current_time.strftime("%Y-%m-%d %H:%M:%S")

    @property
    def seq(self):
        current_seq = self._seq
        self._seq += 1
        return current_seq

    @property
    def cid(self):
        return int(time.time() * 1000)

    @property
    def marker(self):
        return int("900" + str(int(time.time())))

    def _generate_user_agent(self) -> str:
        return json.dumps({
            "ver": 11,
            "cmd": 0,
            "seq": self.seq,
            "opcode": 6,
            "payload": {
                "userAgent": {
                    "deviceType": "WEB",
                    "locale": "ru",
                    "osVersion": "Linux",
                    "deviceName": "Firefox",
                    "headerUserAgent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:135.0) Gecko/20100101 Firefox/135.0",
                    "deviceLocale": "ru",
                    "appVersion": "25.12.1",
                    "screen": "1920x1080 1.0x",
                    "timezone": "Europe/Moscow",
                },
                "deviceId": str(uuid4())
            }
        })

    async def connect(self, _f=None):
        if self._connected:
            return
        
        self.websocket = await websockets.connect(
            uri="wss://ws-api.oneme.ru/websocket",
            origin="https://web.max.ru"
        )
        await self.websocket.send(self.user_agent)
        await self.websocket.recv()

        if _f:
            return

        await self.websocket.send(json.dumps({
            "ver": 11,
            "cmd": 0,
            "seq": self.seq,
            "opcode": 19,
            "payload": {
                "interactive": True,
                "token": self.auth_token,
                "chatsSync": 0,
                "contactsSync": 0,
                "presenceSync": 0,
                "draftsSync": 0,
                "chatsCount": 40
            }
        }))

        p = json.loads(await self.websocket.recv())['payload']
        usr = User(self, p['profile']["contact"])
        self.me = usr
        self._connected = True

        if self._on_connect:
            await self._on_connect()

    async def disconnect(self):
        if not self._connected:
            return
        if self.websocket:
            await self.websocket.close()
            self._seq = 0
        self._connected = False
        self.websocket = None

    def set_token(self, token):
        self.auth_token = token

    async def _heartbeat(self):
        while self._connected and not self._t_stop:
            try:
                await self.websocket.send(json.dumps({
                    "ver": 11,
                    "cmd": 0,
                    "seq": self.seq,
                    "opcode": 1,
                    "payload": {"interactive": False}
                }))
            except Exception as e:
                print("Heartbeat error:", e)
            await asyncio.sleep(30)

    async def run(self):
        await self.connect()
        asyncio.create_task(self._heartbeat())

    async def stop(self):
        self._t_stop = True
        await self.disconnect()

    async def _start_auth(self, phone_number) -> dict:
        await self.connect(_f=1)
        if self.is_log_in:
            raise ValueError("Client is logged in now")

        await self.websocket.send(json.dumps({
            "ver": 11,
            "cmd": 0,
            "seq": self.seq,
            "opcode": 17,
            "payload": {
                "phone": phone_number,
                "type": "START_AUTH",
                "language": "ru"
            }
        }))

        return json.loads(await self.websocket.recv())

    async def _check_code(self, token, code) -> dict:
        await self.websocket.send(json.dumps({
            "ver": 11,
            "cmd": 0,
            "seq": self.seq,
            "opcode": 18,
            "payload": {
                "token": token,
                "verifyCode": code,
                "authTokenType": "CHECK_CODE"
            }
        }))

        token_resp = json.loads(await self.websocket.recv())
        payload = token_resp['payload']
        error = token_resp['payload'].get("error", None)

        if error == "verify.code.wrong":
            raise VerifyCodeWrong(payload["error"], payload["title"])
        return token_resp

    async def auth(self, phone_number: str):
        code_resp = await self._start_auth(phone_number)

        if code_resp.get('payload', {}).get('error'):
            raise ValueError(code_resp['payload']['error'] + ": " + code_resp['payload']['localizedMessage'])

        token = code_resp['payload']['token']
        print(f"Auth token received. Please enter the code sent to your phone.\n")

        while True:
            try:
                code = input("Auth code: ")
                token_resp = await self._check_code(token, code)

                payload = token_resp['payload']
                break

            except VerifyCodeWrong as vcw:
                print(f"{vcw.title} ({vcw.error})")
                continue

            except Exception as e:
                print(e)
                continue

        self.auth_token = payload['tokenAttrs']['LOGIN']['token']
        usr = User(self, payload['profile'])
        self.me = usr
        return self.me

    async def get_chats(self, id: int) -> str:
        seq = self.seq
        if "-" in str(id):
            await self.websocket.send(json.dumps({
                "ver": 11,
                "cmd": 0,
                "seq": seq,
                "opcode": 48,
                "payload": {
                    'chatIds': [id]
                }
            }))
            while True:
                recv = json.loads(await self.websocket.recv())
                if recv["seq"] != seq:
                    pass
                else:
                    break
            title = recv.get('payload').get('chats')[0].get('title')
            return title
        else:
            chat_id = self.me.contact.id ^ id
            j = {
                "ver": 11,
                "cmd": 0,
                "seq": seq,
                "opcode": 32,
                "payload": {
                    "contactIds": [chat_id]
                }
            }
            await self.websocket.send(json.dumps(j))

            while True:
                recv = json.loads(await self.websocket.recv())
                if recv["seq"] != seq:
                    pass
                else:
                    break

            payload = recv["payload"]
            if id:
                contact = payload["contacts"][0]
            return User(self, contact).contact.names[0].name

    async def send_message(self, chat_id: int, text: str, reply_id: str | int = None, notify: bool = True, isrecv: bool = False) -> str:
        seq = self.seq
        j = {
            "ver": 11,
            "cmd": 0,
            "seq": seq,
            "opcode": 64,
            "payload": {
                "chatId": chat_id,
                "message": {
                    "text": text,
                    "cid": self.cid,
                    "elements": [],
                    "attaches": []
                },
                "notify": notify
            }
        }

        if reply_id:
            j["payload"]["message"]["link"] = {
                "type": "REPLY",
                "messageId": str(reply_id)
            }
        await self.websocket.send(json.dumps(j))
        while True:
            recv = json.loads(await self.websocket.recv())
            if recv["seq"] != seq:
                pass
            else:
                break
        try:
            return recv["payload"].get("error")
        except:
            raise

    async def delete_message(self, chat_id: int, message_ids: list[str], for_me: bool = False):
        await self.websocket.send(json.dumps({
            "ver": 11,
            "cmd": 0,
            "seq": self.seq,
            "opcode": 66,
            "payload": {
                "chatId": chat_id,
                "messageIds": message_ids,
                "forMe": for_me
            }
        }))

    async def edit_message(self, chat_id: int, message_id: str | int, text: str):
        seq = self.seq
        await self.websocket.send(json.dumps({
            "ver": 11,
            "cmd": 0,
            "seq": seq,
            "opcode": 67,
            "payload": {
                "chatId": chat_id,
                "messageId": str(message_id),
                "text": text,
                "elements": [],
                "attachments": []
            }
        }))

        while True:
            recv = json.loads(await self.websocket.recv())
            if recv["seq"] != seq:
                pass
            else:
                break
        payload = recv["payload"]
        msg = Message(self, chat_id, **payload["message"])

        return msg

    async def pin_chat(self, chat_id: int | str):
        j = {
            "ver": 11,
            "cmd": 0,
            "seq": self.seq,
            "opcode": 22,
            "payload": {
                "settings": {
                    "chats": {
                        str(chat_id): {
                            "favIndex": int(time.time() * 1000)
                        }
                    }
                }
            }
        }
        await self.websocket.send(json.dumps(j))
        return True

    async def unpin_chat(self, chat_id: int | str):
        j = {
            "ver": 11,
            "cmd": 0,
            "seq": self.seq,
            "opcode": 22,
            "payload": {
                "settings": {
                    "chats": {
                        str(chat_id): {
                            "favIndex": 0
                        }
                    }
                }
            }
        }
        await self.websocket.send(json.dumps(j))
        return True

    async def get_user(self, **kwargs):
        id = kwargs.get('id')
        phone = kwargs.get('phone')
        chat_id = kwargs.get('chat_id')
        _f = kwargs.get("_f")
        seq = self.seq

        if id:
            j = {"ver": 11, "cmd": 0, "seq": seq, "opcode": 32, "payload": {"contactIds": [id]}}
        elif phone:
            j = {"ver": 11, "cmd": 0, "seq": seq, "opcode": 46, "payload": {"phone": str(phone)}}
        elif chat_id:
            id = self.me.contact.id ^ chat_id
            j = {"ver": 11, "cmd": 0, "seq": seq, "opcode": 32, "payload": {"contactIds": [id]}}
        else:
            raise ValueError("no `id` or `phone` or `chat_id` provided")
        await self.websocket.send(json.dumps(j))

        while True:
            recv = json.loads(await self.websocket.recv())
            if recv["seq"] != seq:
                pass
            else:
                break

        payload = recv["payload"]

        error = payload.get("error")

        if error:
            return False

        if id:
            contact = payload["contacts"][0]
        if phone:
            payload["contact"]["phone"] = phone
            contact = payload["contact"]

        return User(self, contact, _f)

    async def session_exit(self):
        j = {
            "ver": 11,
            "cmd": 0,
            "seq": self.seq,
            "opcode": 20,
            "payload": {}
        }
        await self.websocket.send(json.dumps(j))
        await self.disconnect()
        return True

    async def set_reaction(self, chat_id, message_id, reaction: EMOJIS):
        seq = self.seq
        j = {
            "ver": 11,
            "cmd": 0,
            "seq": seq,
            "opcode": 178,
            "payload": {
                "chatId": chat_id,
                "messageId": message_id,
                "reaction": {
                    "reactionType": "EMOJI",
                    "id": reaction
                }
            }
        }
        await self.websocket.send(json.dumps(j))

        while True:
            recv = json.loads(await self.websocket.recv())
            if recv["seq"] != seq:
                pass
            else:
                break

        payload = recv["payload"]
        return Reactions(**payload)

    async def contact_add(self, user_id: int):
        seq = self.seq
        j = {
            "ver": 11,
            "cmd": 0,
            "seq": seq,
            "opcode": 34,
            "payload": {
                "contactId": user_id,
                "action": "ADD"
            }
        }
        await self.websocket.send(json.dumps(j))

        while True:
            recv = json.loads(await self.websocket.recv())
            if recv["seq"] != seq:
                pass
            else:
                break
        payload = recv["payload"]

        return User(self, payload["contact"])

    async def contact_remove(self, user_id: int):
        seq = self.seq
        j = {
            "ver": 11,
            "cmd": 0,
            "seq": seq,
            "opcode": 34,
            "payload": {
                "contactId": user_id,
                "action": "REMOVE"
            }
        }
        await self.websocket.send(json.dumps(j))

        while True:
            recv = json.loads(await self.websocket.recv())
            if recv["seq"] != seq:
                pass
            else:
                break

        return True

    async def contact_block(self, user_id: int):
        seq = self.seq
        j = {
            "ver": 11,
            "cmd": 0,
            "seq": seq,
            "opcode": 34,
            "payload": {
                "contactId": user_id,
                "action": "BLOCK"
            }
        }
        await self.websocket.send(json.dumps(j))

        while True:
            recv = json.loads(await self.websocket.recv())
            if recv["seq"] != seq:
                pass
            else:
                break

        return True

    async def contact_unblock(self, user_id: int):
        seq = self.seq
        j = {
            "ver": 11,
            "cmd": 0,
            "seq": seq,
            "opcode": 34,
            "payload": {
                "contactId": user_id,
                "action": "UNBLOCK"
            }
        }
        await self.websocket.send(json.dumps(j))

        while True:
            recv = json.loads(await self.websocket.recv())
            if recv["seq"] != seq:
                pass
            else:
                break

        return True

    def on_message(self, filters):
        def decorator(func):
            self.handlers.append((filters, func))
            return func

        return decorator

    def on_connect(self, func):
        self._on_connect = func
        return func

    async def download_file(self, chat_id: int, message_id: str, file_id: int) -> str:
        seq = self.seq
        await self.websocket.send(json.dumps({
            "ver": 11,
            "cmd": 0,
            "seq": seq,
            "opcode": 88,
            "payload": {
                "fileId": file_id,
                "chatId": chat_id,
                "messageId": message_id
            }
        }))
        while True:
            recv = json.loads(await self.websocket.recv())
            if recv["seq"] != seq:
                pass
            else:
                break
        url = recv["payload"].get("url")
        return url

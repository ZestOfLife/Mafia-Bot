from __future__ import annotations
from cmdparser import MessageParser
import asyncio
import websockets
import threading
import json
import requests

class WebsocketClient:
    websocket: websockets.client = None
    username: str = None
    password: str = None
    server: str = None
    port: int = None
    sendQueue: list[str] = []
    sendTimer: threading.Timer = None
    messageParser: MessageParser = None
    
    @classmethod
    async def create(self, username: str, password: str, server: str, port: int) -> WebsocketClient:
        self = WebsocketClient()
        self.username = username
        self.password = password
        self.server = server
        self.port = port
        self.websocket = await websockets.connect(f"ws://{server}:{port}/showdown/websocket")
        self.messageParser = MessageParser()
        return self
    
    async def send(self, data: list[str]):
        if self.sendTimer.is_alive() or not self.sendQueue:
            self.sendQueue.extend(data)
        
        self.sendTimer = threading.Timer(0.1, await self.websocket.send, self.sendQueue.pop())
        self.sendTimer.start()
        
    async def recieve(self):
        recv = await self.websocket.recv()
        self.messageParser.parse(recv)
        
    async def login(self):
        challstr = self.messageParser.challstr()
        data = {
                    'name': self.username,
                    'challstr': challstr
        }
        if self.password:
            data['pass'] = self.password
            
        res = requests.post(
            "https://play.pokemonshowdown.com/api/login",
            data=data
        )
        
        if res.status_code == 200:
            assertion = ""
            recv = json.loads(res.text[1:])
            if self.password:
                if recv['actionsucess'] == False:
                    print("Failed to log in :(")
                assertion = recv['assertion']
            else:
                assertion = recv.text
        else:
            print(res.content)
        
        await self.send([f"|/trn {self.username},0,{assertion}"])
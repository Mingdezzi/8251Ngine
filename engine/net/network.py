import asyncio
import websockets
import json
import threading
from asyncio import Queue

class NetworkManager:
    def __init__(self, uri):
        self.uri = uri
        self.websocket = None
        self.incoming_messages = Queue()
        self.outgoing_messages = Queue()
        self.client_id = None
        self.loop = None
        self.thread = None

    def start(self):
        self.thread = threading.Thread(target=self._run_event_loop, daemon=True)
        self.thread.start()

    def _run_event_loop(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(self._run_client())

    async def _run_client(self):
        try:
            async with websockets.connect(self.uri) as websocket:
                self.websocket = websocket
                print("Connected to server.")
                
                initial_message = await websocket.recv()
                data = json.loads(initial_message)
                if data.get('type') == 'id_assignment':
                    self.client_id = data['id']
                    print(f"Assigned Client ID: {self.client_id}")
                
                # 수신 및 송신 핸들러를 동시에 실행
                recv_task = asyncio.create_task(self._receive_handler())
                send_task = asyncio.create_task(self._send_handler())
                await asyncio.gather(recv_task, send_task)
        except Exception as e:
            print(f"Connection failed: {e}")
        finally:
            print("Disconnected from server.")
            self.websocket = None

    async def _receive_handler(self):
        async for message in self.websocket:
            await self.incoming_messages.put(json.loads(message))

    async def _send_handler(self):
        while True:
            message = await self.outgoing_messages.get()
            if self.websocket:
                await self.websocket.send(json.dumps(message))
            self.outgoing_messages.task_done()

    def send(self, data):
        if self.loop:
            self.loop.call_soon_threadsafe(self.outgoing_messages.put_nowait, data)

    def get_messages(self):
        messages = []
        while not self.incoming_messages.empty():
            messages.append(self.incoming_messages.get_nowait())
        return messages

    def stop(self):
        if self.loop:
            self.loop.call_soon_threadsafe(self.loop.stop)
        self.thread.join()

from typing import Dict
from fastapi import WebSocket

class ConnectionManager:
    def __init__(self) -> None:
        # lobby_id -> { player_name: WebSocket }
        self.lobby_connections: Dict[str, Dict[str, WebSocket]] = {}

    async def accept_connection(self, websocket: WebSocket) -> None:
        await websocket.accept()

    def register_connection(self, lobby_id: str, player_name: str, websocket: WebSocket) -> None:
        if lobby_id not in self.lobby_connections:
            self.lobby_connections[lobby_id] = {}
        self.lobby_connections[lobby_id][player_name] = websocket

    def disconnect(self, lobby_id: str, player_name: str) -> None:
        if lobby_id in self.lobby_connections:
            if player_name in self.lobby_connections[lobby_id]:
                del self.lobby_connections[lobby_id][player_name]
            if not self.lobby_connections[lobby_id]:
                del self.lobby_connections[lobby_id]

    async def broadcast_lobby_update(self, lobby_id: str, message: dict) -> None:
        if lobby_id in self.lobby_connections:
            for connection in self.lobby_connections[lobby_id].values():
                await connection.send_json(message)

    async def send_personal_message(self, message: dict, websocket: WebSocket) -> None:
        await websocket.send_json(message)

manager = ConnectionManager()

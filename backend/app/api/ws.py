from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import asyncio
import json
import random

router = APIRouter(prefix="/ws", tags=["WebSockets"])

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

@router.websocket("/simulation")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Simulate real-time environmental data changes
            data = {
                "aqi": round(random.uniform(30.0, 100.0), 1),
                "temperature": round(random.uniform(20.0, 35.0), 1),
                "humidity": round(random.uniform(40.0, 80.0), 1),
                "timestamp": random.randint(1000000, 9999999)
            }
            await manager.broadcast(json.dumps(data))
            await asyncio.sleep(3) # Update every 3 seconds
    except WebSocketDisconnect:
        manager.disconnect(websocket)

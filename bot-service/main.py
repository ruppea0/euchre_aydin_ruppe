import anyio
import redis.asyncio as redis
import os
import random
from bot import BotPlayer

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

async def listen_for_bots(tg: anyio.abc.TaskGroup):
    print(f"Bot service starting, connecting to redis at {REDIS_URL}...")
    r = redis.from_url(REDIS_URL)
    pubsub = r.pubsub()
    await pubsub.subscribe("bot_requests")
    
    print("Listening for bot requests on 'bot_requests' channel...")
    async for message in pubsub.listen():
        if message["type"] == "message":
            lobby_id = message["data"].decode("utf-8")
            print(f"Received request for bot in lobby: {lobby_id}")
            
            # Spawn a new bot
            bot_name = f"Bot_{random.randint(1000, 9999)}"
            print(f"Spawning {bot_name} for lobby {lobby_id}...")
            
            bot = BotPlayer(lobby_id, bot_name)
            tg.start_soon(bot.run)

async def main():
    async with anyio.create_task_group() as tg:
        tg.start_soon(listen_for_bots, tg)

if __name__ == "__main__":
    anyio.run(main)

import asyncio
import asyncpg
from redis.asyncio import Redis
import os

DB_DSN = os.getenv("DB_DSN", "postgresql://postgres:password@localhost:5432/salestorm")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

async def relay():
    conn = await asyncpg.connect(DB_DSN)
    redis = Redis.from_url(REDIS_URL)
    
    print("Started outbox relay worker")
    while True:
        try:
            rows = await conn.fetch("SELECT event_id, event_type, payload FROM outbox WHERE published_at IS NULL LIMIT 100")
            for row in rows:
                event_id = str(row['event_id'])
                payload = row['payload']
                await redis.xadd("events", {"event_type": row['event_type'], "payload": payload, "event_id": event_id})
                await conn.execute("UPDATE outbox SET published_at = now() WHERE event_id = $1", event_id)
        except Exception as e:
            print("Outbox relay error:", e)
        await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(relay())
